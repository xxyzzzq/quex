"""
ABSTRACT:

    The UTF8-State-Split is a procedure introcuded by Frank-Rene Schaefer that
    allows to transform a state machine that triggers on unicode characters
    into a state machine that triggers on the correspondent UTF8 Byte
    Sequences.

PRINCIPLE:

    An elementary trigger in quex state machine is a unicode interval. That
    means, that if a character appears that falls into the interval a state
    transition is triggered. Each of those intervals needs now to be translated
    into interval sequences of the correspondent utf8 byte sequences. A unicode
    transition from state A to state B:

         [ A ]-->(x0, x1)-->[ B ]

    is translated into a chain of utf8-byte sequence transitions that might
    look like this

         [ A ]-->(b0)-->[ 1 ]-->(c0,c1)-->[ B ] 
             \                             /
              `->(d1)-->[ 2 ]---(e0,e1)---' 

    That means that intermediate states may be introduced to reflect the
    different byte sequences that represent the original interval.

IDEAS:
    
    In a simple approach one would translate each element of a interval into an
    utf8-byte sequence and generate state transitions between A and B.  Such an
    approach, however, produces a huge computational overhead and charges the
    later Hopcroft Minimization with a huge state machine.

    To avoid such an overflow, the Hopcroft Minimzation can be prepared on the
    basis of transition intervals. 
    
    (A) Backwards: In somewhat greater intervals, the following might occur:


                 .-->(d1)-->[ 1 ]---(A3,BF)---. 
                /                              \
               /  ,->(d1)-->[ 2 ]---(80,BF)--.  \
              /  /                            \  \
             [ A ]-->(b0)-->[ 3 ]-->(80,BF)-->[ B ] 
                 \                             /
                  `->(d1)-->[ 4 ]---(80,81)---' 

        That means, that for states 2 and 3 the last transition is on [80, BF]
        to state B. Thus, the intermediate states 2 and 3 are equivalent. Both
        can be replaced by a single state. 

    (B) Forwards: The first couple of bytes in the correspondent utf8 sequences
        might be the same. Then, no branch is required until the first differing
        byte.

PROCESS:

    (1) The original interval is split into sub-intervals that have the same 
        length of utf8-byte sequences.

    (2) Each sub-interval is split into further sub-intervals where as 
        many trailing [80,BF] ranges are combined.

    (3) The interval sequences are plugged in between the state A and B
        of the state machine.

(C) 2009 Frank-Rene Schaefer
"""
import os
import sys
from   copy import copy
sys.path.append(os.environ["QUEX_PATH"])

from   quex.engine.misc.utf8                           import utf8_to_unicode, unicode_to_utf8, UTF8_MAX, UTF8_BORDERS
from   quex.engine.misc.interval_handling              import Interval, NumberSet
import quex.engine.state_machine                       as     state_machine
from   quex.engine.state_machine.state.core            import State
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
import quex.engine.state_machine.transformation.common as     common 

utf8_border = [ 0x00000080, 0x00000800, 0x00010000, 0x00110000] 

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
    return common.do(sm, 0x7F, create_intermediate_states)

def do_set(NSet):
    """Unicode values > 0x7F are translated into byte sequences, thus, only number
       sets below that value can be transformed into number sets. They, actually
       remain the same.
    """
    for interval in NSet.get_intervals(PromiseToTreatWellF=True):
        if interval.end > 0x80: return None
    return NSet

def lexatom_n_per_character(CharacterSet):
    """If all characters in a unicode character set state machine require the
    same number of bytes to be represented this number is returned.  Otherwise,
    'None' is returned.

    RETURNS:   N > 0  number of bytes required to represent any character in the 
                      given state machine.
               None   characters in the state machine require different numbers of
                      bytes.
    """
    assert isinstance(CharacterSet, NumberSet)

    interval_list = CharacterSet.get_intervals(PromiseToTreatWellF=True)
    front = interval_list[0].begin     # First element of number set
    back  = interval_list[-1].end - 1  # Last element of number set
    # Determine number of bytes required to represent the first and the 
    # last character of the number set. The number of bytes per character
    # increases monotonously, so only borders have to be considered.
    front_chunk_n = len(unicode_to_utf8(front))
    back_chunk_n  = len(unicode_to_utf8(back))
    if front_chunk_n != back_chunk_n: return None
    else:                             return front_chunk_n

def create_intermediate_states(sm, StateIndex, TargetIndex, Orig):
    transformed_interval_sequence_list = get_interval_sequences(Orig)
    if transformed_interval_sequence_list is None: return False

    plug_interval_sequences(sm, StateIndex, TargetIndex, 
                            transformed_interval_sequence_list)

    return True

def get_interval_sequences(Orig):
    """Orig = Unicode Trigger Set. It is transformed into a sequence of intervals
    that cover all elements of Orig in a representation as UTF8 code units.
    A transition from state '1' to state '2' on 'Orig' is then equivalent to 
    the transitions along the code unit sequence.
    """
    db = split_by_transformed_sequence_length(Orig)
    if db is None: return None

    result = []
    for seq_length, interval in db.items():
        interval_list = get_contiguous_interval_sequences(interval, seq_length)
        result.extend(
            get_trigger_sequence_for_contigous_byte_range_interval(interval, seq_length)
            for interval in interval_list)
    return result

def plug_interval_sequences(sm, StateIndex, TargetIndex, IntervalSequenceList):
    """Plug the 'IntervalSequenceList' into state machine so that it guides 
    from 'StateIndex' to 'TargetIndex'. If the list is greater than '1' it 
    involves the creation of intermediate states.

    ADAPTS: sm[StateIndex] 
            sm, i.e. generates possible new states.
    ___________________________________________________________________________
    Avoiding excessive Hopcroft minimization, the 'IntervalSequenceList' is 
    plugged with some consideration. Imagine two sequences end with [0x80,0xBF]
    triggering to the target state. If for each sequence a separate state
    sequence is implemented this looks like below.

                   (2)---(some)--->(3)---[0x80-0xBF]-->--.
                                                        (4)
                   (5)---(other)-->(6)---[0x80-0xBF]-->--'

    However, state 3 and 6 are equivalent, so the above is equivalent to 

                   (2)---(some)--->(3)---[0x80-0xBF]-->--(4)
                                   /                        
                   (5)---(other)--'                       

    This configuration would also be achieved by Hopcroft Minimization. However,
    here it can be done with a minimal effort. The algorithm stores for each 
    generated state the interval sequence by which the target state is reached, 
    i.e. a database 'iseq_db' maps

           iseq_db:   terminating interval sequence ---> state 'i'

    where state 'i' triggers solely on the 'terminating interval sequence' to 
    'TargetIndex'.
    ___________________________________________________________________________
    """
    tmp_sm = StateMachine()
    for interval_sequence in IntervalSequenceList:
        s_idx  = tmp_sm.init_state_index
        last_i = len(interval_sequence) - 1
        for i, interval in enumerate(interval_sequence):
            if i != last_i: 
                s_idx = tmp_sm.add_transition(s_idx, interval)
            else:           
                tmp_sm.add_transition(s_idx, interval, TargetIndex, AcceptanceF=True)

    tmp_sm = beautifier.do(tmp_sm)
    tmp_target_index = None
    for state_index, state in tmp_sm.states.iteritems():
        if not state.target_map.is_empty(): continue
        tmp_target_index = state_index
        break
    assert tmp_target_index is not None

    # Copy states into the state machine
    for state_index, state in tmp_sm.states.iteritems():
        if   state_index == tmp_sm.init_state_index: continue
        elif state_index == tmp_target_index: continue
        state.target_map.replace_target_index(tmp_target_index, TargetIndex)
        sm.states[state_index] = state

    tmp_init_state = tmp_sm.get_init_state()
    sm.states[StateIndex].set_target_map(tmp_init_state.target_map)
    sm.states[StateIndex].target_map.replace_target_index(tmp_target_index, TargetIndex)

def plug_interval_sequences(sm, StateIndex, TargetIndex, IntervalSequenceList):
    def iseq_db_find_tail(iseq_db, IntervalSequence, TargetIndex):
        """Find a state that has already been created from where some tail
        of 'IntervalSequence' triggers to the 'TargetIndex'.
        """
        found_i = None
        found_state_index = None
        # Iterate from rear to front. 
        for i in reversed(range(len(IntervalSequence))):
            print "#    check:", tuple(IntervalSequence[i:])
            state_index = iseq_db.get(tuple(IntervalSequence[i:]))
            if state_index is None: 
                print "#    failed"
                for key in iseq_db.keys():
                    print "#    key:", key
                break
            found_i = i
            found_state_index = state_index

        print "#  found_i:", found_i
        if found_i is None: return IntervalSequence, TargetIndex
        else:               return IntervalSequence[:found_i], found_state_index

    def plug(iseq_db, sm, IntervalSequence, StateIndex, TargetIndex):
        print "#search:", IntervalSequence
        start_seq, \
        end_state_index = iseq_db_find_tail(iseq_db, IntervalSequence, TargetIndex)
        print "#  found:", end_state_index, start_seq

        # add transition ...
        si     = StateIndex
        last_i = len(start_seq) - 1
        for i, interval in enumerate(start_seq):
            iseq_db[tuple(IntervalSequence[i:])] = si
            print "#enter:", tuple(IntervalSequence[i:]), si 
            if i == last_i: 
                sm.add_transition(si, interval, end_state_index)
                break
            state   = sm.states[si]
            next_si = state.target_map.target_of_exact_interval(interval)
            if next_si is None:
                next_si = sm.add_transition(si, interval)
            si = next_si

        print "#sm:", sm.get_string(Option="hex", NormalizeF=False)

    iseq_db = {}
    for interval_sequence in IntervalSequenceList:
        plug(iseq_db, sm, interval_sequence, StateIndex, TargetIndex)

def split_by_transformed_sequence_length(X):
    """Split Unicode interval into intervals where all values have the same 
    utf8-byte sequence length.

    RETURNS: map: sequence length --> Unicode Sub-Interval of X.
    """
    if X.begin < 0:         X.begin = 0
    if X.end   > UTF8_MAX:  X.end   = UTF8_MAX + 1

    if X.size() == 0: return None

    db = {}
    current_begin = X.begin
    last_L        = len(unicode_to_utf8(X.end - 1))  # Length of utf8 sequence corresponding
    #                                                # the last value inside the interval.
    while 1 + 1 == 2:
        L = len(unicode_to_utf8(current_begin))   # Length of the first unicode in utf8
        # Store the interval together with the required byte sequence length (as key)
        current_end = UTF8_BORDERS[L-1]
        if L == last_L: 
            db[L] = Interval(current_begin, X.end)
            break
        db[L] = Interval(current_begin, current_end)
        current_begin = current_end

    return db
    
def get_contiguous_interval_sequences(X, L):
    """
    A contiguous interval in the domain is an interval where all 'N' first
    lexatoms in the range the same. The last 'N-2' lexatoms cover the whole
    range of lexatom values. The lexatoms at 'N-2' are all adjacent. 'N' may
    range from 1 to 'max. length of lexatom + 1'. In the case 'N=max. length of
    lexatom + 1' only the last by covers a range (if it does).
    
    EXAMPLE: UTF8 sequences related to the unicode interval [0x12345, 0x17653]. 
       
                                                 Sequence Description in 
          Unicode:  UTF8-byte sequence:          Contiguous Interval:

           012345    F0.92.8D.85        ----.
                     ...                    |=>  F0.92.8D.[85-BF]
           01237F    F0.92.8D.BF        ----'   
           012380    F0.92.8E.80        ----.   
                     ...                    |=>  F0.92.[8E-BF].[80-BF]
           012FFF    F0.92.BF.BF        ----'   
           013000    F0.93.80.80        ----.   
                     ...                    |=>  F0.[93-96].[8E-BF].[80-BF]
           016FFF    F0.96.BF.BF        ----'   
           017000    F0.97.80.80        ----.   
                     ...                    |=>  F0.97.[80-98].[80-BF]
           01763F    F0.97.98.BF        ----'   
           017640    F0.97.99.80        ----.   
                     ...                    |=>  F0.97.99.[80-93]
           017653    F0.97.99.93        ----'

    This function splits a given interval into such intervals. Providing such
    intervals and implementing it in state sequences avoids a complex hopcroft 
    minimization after the transformation.

    REQUIRES: The byte sequence in the given interval **must** have all the same 
              length L.

    RETURNS: List of 'contigous' intervals and the index of the first byte
             where all sequences differ.
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
    def min_byte_value(L, ByteIndex):
        assert L <= 6
        if ByteIndex != 0: return 0x80
        # Only first byte's range depends on length
        return { 0: 0x00, 1: 0xC0, 2: 0xE0, 3: 0xF0, 4: 0xF8, 5: 0xFC }[L]

    def max_byte_value(L, ByteIndex):
        assert L <= 6
        if ByteIndex != 0: return 0xBF
        # Only first byte's range depends on length
        return { 0: 0x7F, 1: 0xDF, 2: 0xEF, 3: 0xF7, 4: 0xFB, 5: 0xFD }[L]
       
    def find_first_diff_byte(front_sequence, back_sequence):
        # Find the first byte that is different in the front and back sequence 
        for i in range(L-1):
            if front_sequence[i] != back_sequence[i]: return i
        # At least the last byte must be different. That's why it **must** be the
        # one different if no previous byte was it.
        return L - 1

    assert X.size() != 0

    # Interval's size = 1 character      --> no split
    if X.size() == 1: return [ X ]
    # Resulting utf8 sequence length = 1 --> no split 
    elif L == 1: return [ X ]

    # Utf8 Sequences representing first and last element in interval 'X'.
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
        byte_sequence[q] = max_byte_value(L, q)
        current_end      = utf8_to_unicode(byte_sequence) + 1
        result.append(Interval(current_begin, current_end))
        current_begin    = current_end

    if front_sequence[p] + 1 != back_sequence[p]:
        if p == L - 1: byte_sequence[p] = back_sequence[p]
        else:          byte_sequence[p] = back_sequence[p] - 1 
        current_end      = utf8_to_unicode(byte_sequence) + 1
        result.append(Interval(current_begin, current_end))
        current_begin    = current_end

    byte_sequence[p] = back_sequence[p]
    for q in range(p + 1, L):
        if back_sequence[q] == min_byte_value(L, q):
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
    assert L <= 6

    s_idx = StartStateIdx
    # For the common bytes it is not essential what list is considered, take list no. 0.
    for trigger_set in XList[0][:DIdx]:
        s_idx = sm.add_transition(s_idx, trigger_set)
    # Store the last state where all bytes are the same
    sDIdx = s_idx

    # Indeces of the states that run on 'full range' (frs=full range state)
    def get_sm_index(frs_db, Key):
        result = frs_db.get(Key)
        if result is None: 
            result      = state_machine.index.get()
            frs_db[Key] = result
        return result

    frs_db = {}
    for trigger_set_seq in XList:
        # How many bytes at the end trigger on 'Min->Max'
        sbw_idx  = EndStateIdx
        last_idx = EndStateIdx
        i = L - 1
        while i > DIdx and i != 0:
            if not trigger_set_seq[i].is_equal(FullRange): break
            last_idx = get_sm_index(frs_db, i-1)
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

def get_unicode_range():
    return NumberSet.from_range(0, 0x110000)

def get_codec_element_range():
    """Codec element's size is 1 byte."""
    return NumberSet.from_range(0, 0x100)
