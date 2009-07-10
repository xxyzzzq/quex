import os
import sys
import codecs
sys.path.append(os.environ["QUEX_PATH"])

import quex.input.codec_db as codec_db
import quex.core_engine.utf8 as utf8
from   quex.core_engine.interval_handling import NumberSet, Interval

def do(sm, TrafoInfo, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo != None
    
    return sm.transform(TrafoInfo)
        

def do_set(number_set, TrafoInfo, FH=-1, LineN=None):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    assert TrafoInfo != None
    
    return number_set.transform(TrafoInfo)
        

def do_utf8_state_split(sm):
    """The UTF8 encoding causes a single unicode character code being translated
       into a sequence of bytes. A state machine triggering on unicode characters
       can be converted into a state machine triggering on UTF8 bytes.

       For this a simple transition on a character 'X':

            [ 1 ]---( X )--->[ 2 ]

       needs to be translated into a sequence of state transitions

            [ 1 ]---(x0)--->[ S0 ]---(x1)--->[ S1 ]---(x2)--->[ 2 ]

       where, x0, x1, x2 are the UTF8 bytes that represent unicode 'X'. 
       States S0 and S1 are intermediate states created only so that
       x1, x2, and x3 can trigger. Note, that the UTF8 sequence ends
       at the same state '2' as the previous single trigger 'X'.
    """
    def create_states(sm, N):
        index_list = []
        for i in range(N):
            sm.states[state_index] = state_machine.State(StateMachineID = sm.get_id(),
                                                         StateID        = state_index)
            index_list.append(state_index)
        return index_list

    for original_start_state_index, state in sm.states.items():
        # Get the 'transition_list', i.e. a list of pairs (TargetState, NumberSet)
        # which indicates what target state is reached via what number set.
        transition_list = state.transitions().get_map().items()
        # Clear the state's transitions, now. This way it can absorb new
        # transitions to intermediate states.
        state.transitions().clear()
        # Loop over all transitions
        for original_target_state_index, number_set in transition_list:
            # We take the intervals with 'PromiseToTreatWellF' even though they
            # are changed. This is because the intervals would be lost anyway
            # after the state split, so we use the same memory and do not 
            # cause a time consuming memory copy and constructor calls.
            interval_list = number_set.get_intervals(PromiseToTreatWellF=True)
            db = do_utf8_number_set_split(interval_list)
            # Connect 
            for interval in db.values():
                trigger_set_sequence = translate_unicode_interval_into_utf8_trigger_sequence(interval)

                state_index = original_start_state_index
                for trigger_set in trigger_set_sequence[:-1]:
                    state_index = sm.add_transition(state_index, trigger_set)

                # The last trigger set triggers to the original target state
                sm.add_transition(state_index, trigger_set_sequence[-1], original_target_state_index)

utf8c = codecs.getencoder("utf-8")
utf8d = codecs.getdecoder("utf-8")
def unicode_to_utf8(UnicodeValue):
    return map(ord, utf8c(unichr(UnicodeValue))[0])

def utf8_to_unicode(ByteSequence):
    return ord(utf8d(reduce(lambda x, y: x + y, map(chr, border_sequence))))

def translate_unicode_interval_into_utf8_trigger_sequence(X):
    front_list = unicode_to_utf8(X.begin)
    back_list  = unicode_to_utf8(X.end - 1)
    return map(lambda front, back: Interval(front, back + 1), front_list, back_list)

def do_utf8_number_set_split(NSet):
    """Identify intervals that belong to the same UTF8 byte formatting range
       That means, that identify sub-ranges where only the last formatted
       byte changes. These ranges can be replaced by a sequence:


            [ 1 ]---(x0)--->[ S0 ]---(x1)--->[ S1 ]---{X2}--->[ 2 ]

       Where {X2} is the set of changing bytes that belong to the range.
    """
    assert not NSet.is_empty()

    interval_list = NSet.get_intervals() 
    result        = {}
    for interval in interval_list:
        i_db = split_interval_according_to_utf8_byte_sequence_length(interval)
        for n, sub_interval in i_db.items():
            eq_interval_list = split_interval_into_equivalence_byte_ranges(sub_interval)
            result.setdefault(n, []).extend(eq_interval_list)

    return result

        
def split_interval_according_to_utf8_byte_sequence_length(X):
    """Split Unicode interval into intervals where all values
       have the same utf8-byte sequence length.
    """
    assert X.end <= 0x10FFFF  # Interval must lie in unicode range

    utf8_border = [ 0x00000080, 0x00000800, 0x00010000, 0x0010FFFF] 
    db = {}
    new_interval = X
    while new_interval != None:
        interval = new_interval
        L0 = len(unicode_to_utf8(interval.begin))   # Length of the first unicode in utf8
        L1 = len(unicode_to_utf8(interval.end - 1)) # Length of the last unicode in utf8
        if L0 != L1: 
            next_border  = utf8_border[L0]
            new_interval = Interval(next_border, interval.end)
            interval.end = next_border
        else:
            new_interval = None
        # Store the interval together with the required byte sequence length (as key)
        db[L0] = interval
    return db
    
def split_interval_into_equivalence_byte_ranges(L, X):
    """ X   Unicode interval where all utf8 byte sequences have 
            the same length.
    
        L   Sequence Length of all utf8 byte sequences in X.
    """
    #    1 byte  - 0xxxxxxx
    #    2 bytes - 110xxxxx 10xxxxxx
    #    3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
    #    4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
    #    5 bytes ... 
    def begin_of_byte_range(ByteIndex, SequenceLength):
        if ByteIndex == 0:
            return { 0: 0x00, 1: 0xC0, 2: 0xE0, 3: 0xF0 }[SequenceLength]
        return 0x80
    def end_of_byte_range(ByteIndex, SequenceLength):
        if ByteIndex == 0:
            return { 0: 0x7F, 1: 0xDF, 2: 0xEF, 3: 0xF7 }[SequenceLength]
        return 0xBF
       
    def check_split(X):
        if X.size() == 1: return -1

        front_sequence = unicode_to_utf8(interval.begin)
        back_sequence  = unicode_to_utf8(interval.end - 1)
        # Find the first byte that is different in the front and back sequence 
        for i in range(L):
            if begin_sequence[i] != end_sequence[i]: break

        # If the remaining bytes all span the whole range, than no split is necessary.
        if i == L - 1: return -1

        for k in range(i):
            if front_sequence[k] != front_of_byte_range(k, L): break
            if back_sequence[k]  != back_of_byte_range(k, L): break
        else:
            return -1

        # Return the border unicode that results in an equivalence 
        # interval together with 'begin'.
        border_sequence = front_sequence[:i]
        border_sequence.append(front_sequence[i] + 1) 
        for k in range(i+1, L):
            border_sequence.append(begin_of_byte_range(k, L))
        return utf8_to_unicode(border_sequence)

    result = []
    interval = X
    while interval != None:
        border_value = split_if_necessary(interval)
        if border_value == -1: 
            result.append(interval)
            break
        else:
            result.append(Interval(interval.begin, border_value + 1))
            interval.begin = border_value


