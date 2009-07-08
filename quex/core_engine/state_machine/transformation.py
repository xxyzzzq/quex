import os
import sys
sys.path.append(os.environ["QUEX_PATH"])

import quex.input.codec_db as codec_db

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
            state_index = state_machine.index.get()
            sm.states[state_index] = state_machine.State(StateMachineID = sm.get_id(),
                                                         StateID        = state_index)
            index_list.append(state_index)
        return index_list

    for state_index, state in sm.states.items():
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
            # Find the number of required intermediate states
            intermediate_state_n = max(db.keys())
            # Get the intermediate states
            intermediate_state_index_list = create_states(sm, intermediate_state_n)

            # Connect 
            for interval in interval_list:
                begin_utf8_sequence = utf8_sequence(interval.begin)
                end_utf8_sequence   = utf8_sequence(interval.end)
                # According to the previous sorting: The first bytes are all equal
                i = -1
                for byte in begin_utf8_sequence[:-1]:
                    i += 1
                    sm.states[state_index].transitions().add_transition(byte, intermediate_state_index_list[i])
                # The last byte might span a range--add it.
                last_byte_interval = Interval(begin_utf8_sequence[-1], end_utf8_sequence[-1]) 
                sm.states[state_index].transitions().add_transition(last_byte_interval,
                                                                    original_target_state_index)

def do_utf8_number_set_split(NSet):
    """Identify intervals that belong to the same UTF8 byte formatting range
       That means, that identify sub-ranges where only the last formatted
       byte changes. These ranges can be replaced by a sequence:


            [ 1 ]---(x0)--->[ S0 ]---(x1)--->[ S1 ]---{X2}--->[ 2 ]

       Where {X2} is the set of changing bytes that belong to the range.
    """
    def utf8_sequence(UnicodeValue):
        return map(ord, map_unicode_to_utf8(UnicodeValue)))

    def unicode_value_where_last_utf8_byte_overflows(UnicodeValue, UTF8_ByteSequence):
        """UnicodeValue is the unicode code pointer that corresponds to the given
           UTF8_ByteSequence.
        """
        L = len(UTF8_ByteSequence)
        last_byte = UTF8_ByteSequence[-1]
        # UTF8 Character sequences look like the following:
        #
        #    1 byte  - 0xxxxxxx
        #    2 bytes - 110xxxxx 10xxxxxx
        #    3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
        #    4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
        #    5 bytes ... 
        # 
        # That is: If L == 1, only the first bit is a mask bit and the remaining 7 are
        #                     data bits. The maximum value for the last byte is 0x7F.
        #          If L > 1, then only the last 6 bit are data bit and the mask is always
        #                    '10'. Thus the maximum value for the last byte is 0xBF.
        #
        if L == 1: last_byte_overflow_value = 0x7F
        else:      last_byte_overflow_value = 0xBF
        # 
        # The computation of the 'border unicode character' before the overflow solely
        # based on the byte sequence might be cumbersome. Since, it is already known
        # what unicode character belongs to the sequence, and since the value distribution
        # is monotoneously increasing, let us use the simpler formular:
        #
        # end_unicode_value = ...
        return UnicodeValue + (last_byte_overflow_value - last_byte) + 1

    interval_list = NSet.get_intervals() 
    size = interval_list
    i    = -1
    while i != size:
        i += 1
        interval       = interval_list[i]
        begin_utf8_seq = utf8_sequence(interval.begin)
        border_unicode_value = unicode_value_where_last_utf8_byte_overflows(interval.begin, begin_utf8_seq)
        if interval.end > border_unicode_value: 
            # -- New interval from 'border_unicode_value' to old interval enters the 
            #    discussion.
            # -- Set the end of the old interval to the 'border_unicode_value', so that the
            #    old interval causes no change in the last but one byte.
            new_interval = Interval(border_unicode_value, interval.end)
            interval.end = border_unicode_value

            interval_list.append(new_interval)
            size += 1
        else:
            # Interval [begin, end) does not change its last but one byte in the sequence.
            pass

        byte_sequence_length = len(utf8_sequence(interval_begin.begin))
        db.getdefaul(byte_sequence_length - 1, []).append(interval)

    return db

        
    

