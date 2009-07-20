# (C) 2009 Frank-Rene Schaefer
"""
ABSTRACT:

    !! UTF16 state split is similar to UTF8 state split as shown in file !!
    !! "uf8_state_split.py". Please, read the documentation thera about  !!
    !! the details of the basic idea.                                    !!

    Due to the fact that utf16 conversion has only two possible byte
    sequence lengths, 2 and 4 bytes, the state split process is 
    significantly easier than the utf8 stae split.

    The principle idea remains: A single transition from state A to
    state B is translated (sometimes) into an intermediate state
    transition to reflect that the unicode point is represent by
    a value sequence.

    The special case utf16 again is easier, since, for any unicode point <=
    0xFFFF the representation value remains exactly the same, thus those
    intervals do not have to be adapted at all!
    
    Further, it does not make sense to identify 'contigous' intervals 
    where the last value runs repeatedly from min to max, since the 
    intervals are of size 0x10000 which is pretty large and the probability
    that a range runs over multiple such ranges is low (even if so, it
    could be at max. 17 such intervals since unicode values end at 0x110000).
"""
import os
import sys
import codecs
from copy import copy
sys.path.append(os.environ["QUEX_PATH"])

from   quex.core_engine.interval_handling        import Interval
import quex.core_engine.state_machine            as     state_machine
from   quex.core_engine.state_machine.core       import State
import quex.core_engine.state_machine.nfa_to_dfa as     nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization as hopcroft_minimization

ForbiddenRange = Interval(0xD800, 0xDC00)

def do(sm):
    state_list = sm.states.items()
    for state_index, state in state_list:
        # Get the 'transition_list', i.e. a list of pairs (TargetState, NumberSet)
        # which indicates what target state is reached via what number set.
        transition_list = state.transitions().get_map().items()
        # Clear the state's transitions, now. This way it can absorb new
        # transitions to intermediate states.
        state.transitions().clear()
        # Loop over all transitions
        for target_state_index, number_set in transition_list:
            # We take the intervals with 'PromiseToTreatWellF' even though they
            # are changed. This is because the intervals would be lost anyway
            # after the state split, so we use the same memory and do not 
            # cause a time consuming memory copy and constructor calls.
            interval_list = number_set.get_intervals(PromiseToTreatWellF=True)

            # 1st check wether a modification is necessary
            modification_required_f = False
            for interval in interval_list:
                if interval.begin >= 0x10000: modification_required_f = True; break

            if modification_required_f == False:
                sm.states[state_index].add_transition(number_set, target_state_index)
                continue

            # Now, intermediate states may be added
            for interval in interval_list:
                create_intermediate_states(sm, state_index, target_state_index, interval)

    return hopcroft_minimization.do(nfa_to_dfa.do(sm), CreateNewStateMachineF=False)

def do_set(NSet):
    """Unicode values > 0xFFFF are translated into byte sequences, thus, only number
       sets below that value can be transformed into number sets. They, actually
       remain the same.
    """
    for interval in NSet.get_intervals(PromiseToTreatWellF=True):
        if interval.end > 0x10000: return None
    return NSet

def create_intermediate_states(sm, StartStateIdx, EndStateIdx, X):
    # Split the interval into a range below and above 0xFFFF. This corresponds
    # unicode values that are represented in utf16 via 2 and 4 bytes (1 and 2 words).
    interval_1word, interval_2words = split_interval_according_to_sequence_length(X)

    if interval_1word != None:
        sm.add_transition(StartStateIdx, interval_1word, EndStateIdx)

    if interval_2words != None:
        # Introduce intermediate state
        trigger_seq = get_trigger_sequence_for_interval(interval_2words)
        s_idx = sm.add_transition(StartStateIdx, trigger_seq[0])
        sm.add_transition(s_idx, trigger_seq[1], EndStateIdx)

utf16c = codecs.getencoder("utf-16be")
def unicode_to_utf16(UnicodeValue):
    byte_seq = map(ord, utf16c(unichr(UnicodeValue))[0])
    if UnicodeValue >= 0x10000:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1], (byte_seq[2] << 8) + byte_seq[3] ]
    else:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1] ]

    return word_seq

def split_interval_according_to_sequence_length(X):
    """Split Unicode interval into intervals where all values
       have the same utf16-byte sequence length. This is fairly 
       simple in comparison with utf8-byte sequence length: There
       are only two lengths: 2 bytes and 2 x 2 bytes.

       RETURNS:  [List0, List1]  

                 with List0 being the sub-interval where all values are 2
                 byte utf16 encoded, and List1 being the sub-interval where 
                 all values are 4 byte utf16 encoded.
    """
    global ForbiddenRange
    if X.begin == -sys.maxint: X.begin = 0
    if X.end   == sys.maxint:  X.end   = 0x110000
    assert X.end <= 0x110000                 # Interval must lie in unicode range
    assert not X.check_touch(ForbiddenRange) # The 'forbidden range' is not to be covered.

    if X.end < 0x10000:      return [X, None]
    elif X.begin >= 0x10000: return [None, X]
    else:                    return [Interval(X.begin, 0x10000), Interval(0x10000, X.end)]
    
def get_trigger_sequence_for_interval(X):
    # The interval either lies entirely >= 0x10000 or entirely < 0x10000
    assert X.begin >= 0x10000 or X.end < 0x10000

    # An interval below < 0x10000 remains the same
    if X.end < 0x10000: return [ X ]
    
    # In case that the interval >= 0x10000 it the value is split up into
    # two values.
    front_seq = unicode_to_utf16(X.begin)
    back_seq  = unicode_to_utf16(X.end - 1)

    return [ Interval(front_seq[0], back_seq[0] + 1), 
             Interval(front_seq[1], back_seq[1] + 1) ]
    


