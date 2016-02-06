"""
ABSTRACT:

The 'State-Split' is a procedure introcuded by Frank-Rene Schaefer that allows
to transform a state machine that triggers on some 'pure' values (e.g. Unicode
Characters) into a state machine that triggers on the sequences (e.g. UTF8 Code
Units) that correspond to the original values. This procedure is to be used for
encodings of dynamic size, i.e. where the number of code units to represent a
'pure' value changes depending on the value itself (e.g. UTF8, UTF16).

PRINCIPLE:

A state transition is described by a 'trigger set' and a target state.
If an input occurs that belongs to the 'trigger set' the state machine
transits into the specific target state. Trigger sets are composed
of one ore more contiguous intervals. An interval spans a set of 'pure'
values. A pure value represented in a different codec by a sequence.

An elementary trigger in quex state machine is an interval.  If an input
lexatom appears that falls into the interval a specific state transition is
triggered.  Each of those intervals needs now to be translated into interval
sequences of the correspondent utf8 byte sequences. A unicode transition from
state A to state B:

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
"""

import quex.engine.state_machine.algorithm.beautifier as     beautifier

def do(sm, UnchangedRange, get_interval_sequences, prune=lambda x: None):
    """A single unicode character code is translated into a sequence of 
    bytes. Example: For this a simple transition on a character 'X':

            [ 1 ]---( X )--->[ 2 ]

    needs to be translated into a sequence of state transitions

            [ 1 ]---(x0)--->[ S0 ]---(x1)--->[ S1 ]---(x2)--->[ 2 ]

    where, x0, x1, x2 are the UTF8 bytes that represent unicode 'X'.
    States S0 and S1 are intermediate states created only so that x1, x2,
    and x3 can trigger. UTF8 sequence ends at the same state '2' as the 
    previous single trigger 'X'.
    """
    state_list = sm.states.items()
    for state_index, state in state_list:
        # Safe-copy 'transition_list', i.e. a list of pairs (TargetState, NumberSet).
        # => which target state is reached via what number set.
        transition_list = state.target_map.get_map().items()
        # Clear the state's transitions. 
        # => Ready to absorbe new transitions.
        state.target_map.clear()
        # Loop over all transitions
        for target_state_index, number_set in transition_list:
            # Check whether a modification is necessary
            if number_set.supremum() <= UnchangedRange:
                sm.states[state_index].add_transition(number_set, target_state_index)
                continue

            # Cut out any forbiddin range. Assume, that is has been checked
            # before, or is tolerated to be omitted.
            prune(number_set)

            # Take intervals with 'PromiseToTreatWellF' even though they 
            # are changed. They were lost anyway after state split! 
            for interval in number_set.get_intervals(PromiseToTreatWellF=True):
                create_intermediate_states(sm, state_index, target_state_index, interval,
                                            get_interval_sequences)

    return beautifier.do(sm)

def create_intermediate_states(sm, StateIndex, TargetIndex, Orig,
                               get_interval_sequences):
    transformed_interval_sequence_list = get_interval_sequences(Orig)
    if transformed_interval_sequence_list is None: return False

    plug_interval_sequences(sm, StateIndex, TargetIndex, 
                            transformed_interval_sequence_list)

    return True

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
    def iseq_db_find_tail(iseq_db, IntervalSequence, TargetIndex):
        """Find a state that has already been created from where some tail
        of 'IntervalSequence' triggers to the 'TargetIndex'.
        """
        found_i = None
        found_state_index = None
        # Iterate from rear to front. 
        for i in reversed(range(len(IntervalSequence))):
            ##print "#    check:", tuple(IntervalSequence[i:])
            state_index = iseq_db.get(tuple(IntervalSequence[i:]))
            if state_index is None: 
                ##print "#    failed"
                ##for key in iseq_db.keys():
                    ##print "#    key:", key
                break
            found_i = i
            found_state_index = state_index

        ##print "#  found_i:", found_i
        if found_i is None: return IntervalSequence, TargetIndex
        else:               return IntervalSequence[:found_i], found_state_index

    def plug(iseq_db, sm, IntervalSequence, StateIndex, TargetIndex):
        ##print "#search:", IntervalSequence
        start_seq, \
        end_state_index = iseq_db_find_tail(iseq_db, IntervalSequence, TargetIndex)
        ##print "#  found:", end_state_index, start_seq

        # add transition ...
        si     = StateIndex
        last_i = len(start_seq) - 1
        for i, interval in enumerate(start_seq):
            iseq_db[tuple(IntervalSequence[i:])] = si
            ##print "#enter:", tuple(IntervalSequence[i:]), si 
            if i == last_i: 
                sm.add_transition(si, interval, end_state_index)
                break
            state   = sm.states[si]
            next_si = state.target_map.target_of_exact_interval(interval)
            if next_si is None:
                next_si = sm.add_transition(si, interval)
            si = next_si

        ##print "#sm:", sm.get_string(Option="hex", NormalizeF=False)

    iseq_db = {}
    for interval_sequence in IntervalSequenceList:
        plug(iseq_db, sm, interval_sequence, StateIndex, TargetIndex)

