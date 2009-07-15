# (C) 2009 Frank-Rene Schaefer
import os
import sys
import codecs
from copy import copy
sys.path.append(os.environ["QUEX_PATH"])

from   quex.core_engine.interval_handling  import Interval
import quex.core_engine.state_machine      as     state_machine
from   quex.core_engine.state_machine.core import State

def do(sm):
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
    return ord(utf8d(reduce(lambda x, y: x + y, map(chr, ByteSequence)))[0])

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
    assert X.end <= 0x110000  # Interval must lie in unicode range

    utf8_border = [ 0x00000080, 0x00000800, 0x00010000, 0x00110000] 
    db = {}
    current_begin = X.begin
    LastL = len(unicode_to_utf8(X.end - 1))  # Length of utf8 sequence corresponding
    #                                        # the last value inside the interval.
    while 1 + 1 == 2:
        L = len(unicode_to_utf8(current_begin))   # Length of the first unicode in utf8
        # Store the interval together with the required byte sequence length (as key)
        current_end = utf8_border[L-1]
        if L == LastL: 
            db[L] = Interval(current_begin, X.end)
            break
        db[L] = Interval(current_begin, current_end)
        current_begin = current_end

    return db
    
def split_interval_into_contigous_byte_sequence_range(X, L):
    """
       DEFINITION: 'Contigous Byte Sequence Range'
    
        is a contigous interval specified by [begin, end) where all values
        in between begin and end have the following property:

           The utf8 sequence of each value has the following shape:
 
             [byte 0][byte 1] ... [byte p   ] ...

             same --------------->|different| ...

           Further, the union of [byte q], where p < q < L, spans
           the whole byte range. The idea behind it is that such an
           interval can be translated into a state sequence

           (1)--[byte0]-->(2)--[byte1]-->(3)--[byte's k]-->(4)--[Range]-->(5)--[Range]--
    
        ARGUMENTS: 
    
            X   Unicode interval where all utf8 byte sequences have 
                the same length.
        
            L   The actual length all utf8 byte sequences for values in X.

        ALGORITHM: 

        -- The result is stored in a list, the list of intervals where
           each interval falls into an contigous byte range. 

        -- The 'interval' is investigated if it fullfills the above
           criteria. If not the value is returned, so that the interval
           can be split into:

             (1) 
           
            

    """
    # A byte in a utf8 sequence can only have a certain range depending
    # on its position. UTF8 sequences look like the following dependent
    # on their length:
    #
    #       Length:   Byte Masks for each byte
    #
    #       1 byte    0xxxxxxx
    #       2 bytes   110xxxxx 10xxxxxx
    #       3 bytes   1110xxxx 10xxxxxx 10xxxxxx
    #       4 bytes   11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
    #       5 bytes   ...
    #
    # where 'free' bits are indicated by 'x'. 
    # Min. value of a byte = where all 'x' are zero.
    # Max. value of a byte = where all 'x' are 1.
    # 
    def min_byte_value(ByteIndex):
        if ByteIndex == 0:
            return { 0: 0x00, 1: 0xC0, 2: 0xE0, 3: 0xF0 }[L]
        return 0x80

    def max_byte_value(ByteIndex):
        if ByteIndex == 0:
            return { 0: 0x7F, 1: 0xDF, 2: 0xEF, 3: 0xF7 }[L]
        return 0xBF
       
    def find_first_diff_byte(front_sequence, back_sequence):
        # Find the first byte that is different in the front and back sequence 
        for i in range(L-1):
            if front_sequence[i] != back_sequence[i]: return i
        # At least the last byte must be different. That's why it **must** be the
        # one different if no previous byte was it.
        return L - 1

    assert X.size() != 0

    if X.size() == 1: return [ X ]
    # If the utf8 sequence consist of one byte, then the range cannot be split.
    if L == 1: return [ X ]

    front_sequence = unicode_to_utf8(X.begin)
    back_sequence  = unicode_to_utf8(X.end - 1)
    p      = find_first_diff_byte(front_sequence, back_sequence)
    result = []
    current_begin = X.begin
    byte_sequence = copy(front_sequence)
    byte_indeces  = range(p + 1, L)
    byte_indeces.reverse()
    for q in byte_indeces:
        # There **must** be at least one overrun, even for 'q=p+1', since 'p+1' 
        # indexes the first byte after the first byte that was different. If 'p' 
        # indexed that last byte this block is never entered.
        byte_sequence[q] = max_byte_value(q)
        current_end      = utf8_to_unicode(byte_sequence) + 1
        result.append(Interval(current_begin, current_end))
        current_begin    = current_end

    if front_sequence[p] + 1 != back_sequence[p]:
        if p == L - 1: byte_sequence[p] = back_sequence[p]
        else:          byte_sequence[p] = back_sequence[p] - 1 
        current_end      = utf8_to_unicode(byte_sequence) + 1
        ## print "##begin: ", ["%02X" % x for x in unicode_to_utf8(current_begin)]
        ## print "##end-1: ", ["%02X" % x for x in unicode_to_utf8(current_end - 1)]
        result.append(Interval(current_begin, current_end))
        current_begin    = current_end

    byte_sequence[p] = back_sequence[p]
    for q in range(p + 1, L):
        if back_sequence[q] == min_byte_value(q):
            byte_sequence[q] = back_sequence[q]
        else:
            if q == L - 1: byte_sequence[q] = back_sequence[q] 
            else:          byte_sequence[q] = back_sequence[q] - 1
            current_end      = utf8_to_unicode(byte_sequence) + 1
            result.append(Interval(current_begin, current_end))
            if current_begin == X.end: break
            current_begin    = current_end
            byte_sequence[q] = back_sequence[q]


    if current_begin != X.end:
        result.append(Interval(current_begin, X.end))

    return result

def get_trigger_sequence_for_contigous_byte_range_interval(X, L):
    front_sequence = unicode_to_utf8(X.begin)
    back_sequence  = unicode_to_utf8(X.end - 1)
    # If the interval is contigous it must produce equal length utf8 sequences

    # Let me play with 'list comprehensions' just one time
    return [ Interval(front_sequence[i], back_sequence[i] + 1) for i in range(L) ]


# For byte n > 1, the max byte range is always 0x80-0xBF (including 0xBF)
FullRange = Interval(0x80, 0xC0)
def plug_state_sequence_for_trigger_set_sequence(sm, StartStateIdx, EndStateIdx, XList, L, DIdx):
    """Create a state machine sequence for trigger set list of the same length.

       L      Length of the trigger set list.
       DIdx   Index of first byte that differs, i.e. byte[i] == byte[k] for i, k < DIdx.
       XList  The trigger set list.

                                    .          .              .
                       [A,         B,         C,         80-BF  ] 

              [Start]--(A)-->[1]--(B)-->[2]--(C)-->[3]--(80-BF)-->[End]
    """
    global FullRange
    assert L < 5

    s_idx = StartStateIdx
    # For the common bytes it is not essential what list is considered, take list no. 0.
    for trigger_set in XList[0][:DIdx]:
        s_idx = sm.add_transition(s_idx, trigger_set)
    # Store the last state where all bytes are the same
    sDIdx = s_idx

    # Indeces of the states that run on 'full range' (frs=full range state)
    frs_idx = [ state_machine.index.get(), state_machine.index.get(), state_machine.index.get() ]

    for trigger_set_seq in XList:
        # How many bytes at the end trigger on 'Min->Max'
        sbw_idx = EndStateIdx
        last_idx = EndStateIdx
        i = L - 1
        while i > DIdx and i != 0:
            if not trigger_set_seq[i].is_equal(FullRange): break
            last_idx = frs_idx[i-1]
            if not sm.states.has_key(last_idx): sm.states[last_idx] = State()
            sm.add_transition(last_idx, trigger_set_seq[i], sbw_idx)
            sbw_idx = last_idx
            i -= 1

        sbw_idx = last_idx
        while i > DIdx:
            # Maybe, it has already a transition on trigger_set .. (TO DO)
            last_idx = state_machine.index.get()
            sm.add_transition(last_idx, trigger_set_seq[i], sbw_idx)
            sbw_idx = last_idx
            i -= 1

        sm.add_transition(sDIdx, trigger_set_seq[i], last_idx)

    return       


       

