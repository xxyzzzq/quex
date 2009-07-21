# (C) 2009 Frank-Rene Schaefer
"""
ABSTRACT:

    !! UTF16 state split is similar to UTF8 state split as shown in file !!
    !! "uf8_state_split.py". Please, read the documentation thera about  !!
    !! the details of the basic idea.                                    !!

    Due to the fact that utf16 conversion has only two possible byte sequence
    lengths, 2 and 4 bytes, the state split process is significantly easier
    than the utf8 stae split.

    The principle idea remains: A single transition from state A to state B is
    translated (sometimes) into an intermediate state transition to reflect
    that the unicode point is represent by a value sequence.

    The special case utf16 again is easier, since, for any unicode point <=
    0xFFFF the representation value remains exactly the same, thus those
    intervals do not have to be adapted at all!
    
    Further, the identification of 'contigous' intervals where the last value
    runs repeatedly from min to max is restricted to the consideration of a
    single word. UTF16 character codes can contain at max two values (a
    'surrogate pair') coded in two 'words' (1 word = 2 bytes). The overun
    happens every 2*10 code points.  Since such intervals are pretty large and
    the probability that a range runs over multiple such ranges is low, it does
    not make sense to try to combine them. The later Hopcroft Minimization will
    not be overwhelmed by a little extra work.

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

    result = hopcroft_minimization.do(nfa_to_dfa.do(sm), CreateNewStateMachineF=False)
    return result

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
    interval_1word, intervals_2word = get_contigous_intervals(X)

    if interval_1word != None:
        sm.add_transition(StartStateIdx, interval_1word, EndStateIdx)

    if intervals_2word != None:
        for interval in intervals_2word:
            # Introduce intermediate state
            trigger_seq = get_trigger_sequence_for_interval(interval)
            s_idx = sm.add_transition(StartStateIdx, trigger_seq[0])
            sm.add_transition(s_idx, trigger_seq[1], EndStateIdx)

utf16c = codecs.getencoder("utf-16be")

def unicode_to_utf16(UnicodeValue):
    """Do not do this by hand in order to have a 'reference' to double check
       wether otherwise hand coded values are correct.
    """
    byte_seq = map(ord, utf16c(unichr(UnicodeValue))[0])
    if UnicodeValue >= 0x10000:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1], (byte_seq[2] << 8) + byte_seq[3] ]
    else:
        word_seq = [ (byte_seq[0] << 8) + byte_seq[1] ]

    return word_seq

def utf16_to_unicode(WordSeq):
    if len(WordSeq) == 1: return WordSeq[0]

    x0 = WordSeq[0] - 0xD800
    x1 = WordSeq[1] - 0xDC00

    return (x0 << 10) + x1 + 0x10000

def get_contigous_intervals(X):
    """Split Unicode interval into intervals where all values
       have the same utf16-byte sequence length. This is fairly 
       simple in comparison with utf8-byte sequence length: There
       are only two lengths: 2 bytes and 2 x 2 bytes.

       RETURNS:  [X0, List1]  

                 X0   = the sub-interval where all values are 1 word (2 byte)
                        utf16 encoded. 
                         
                        None => No such interval
                
                List1 = list of contigous sub-intervals where coded as 2 words.

                        None => No such intervals
    """
    global ForbiddenRange
    if X.begin == -sys.maxint: X.begin = 0
    if X.end   == sys.maxint:  X.end   = 0x110000
    assert X.end <= 0x110000                 # Interval must lie in unicode range
    assert not X.check_touch(ForbiddenRange) # The 'forbidden range' is not to be covered.

    if X.end < 0x10000:      return [X, []]
    elif X.begin >= 0x10000: return [None, split_contigous_intervals_for_surrogates(X.begin, X.end)]
    else:                    return [Interval(X.begin, 0x10000), split_contigous_intervals_for_surrogates(0x10000, X.end)]

def split_contigous_intervals_for_surrogates(Begin, End):
    """Splits the interval X into sub interval so that no interval runs over a 'surrogate'
       border of the last word. For that, it is simply checked if the End falls into the
       same 'surrogate' domain of 'front' (start value of front = Begin). If it does not
       an interval [front, end_of_domain) is split up and front is set to end of domain.
       This procedure repeats until front and End lie in the same domain.
    """
    assert Begin >= 0x10000
    assert End   <= 0x110000

    front_seq = unicode_to_utf16(Begin)
    back_seq  = unicode_to_utf16(End - 1)

    result = []
    front  = Begin
    while front_seq[0] != back_seq[0]:
        end_of_domain = utf16_to_unicode([front_seq[0], 0xDFFF]) + 1
        result.append(Interval(front, end_of_domain))
        if end_of_domain >= End: break
        front_seq[0] = front_seq[0] + 1
        front_seq[1] = 0
        front        = end_of_domain

    if front < End:
        result.append(Interval(front, End))

    return result
    
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
    


