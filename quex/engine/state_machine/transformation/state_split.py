"""State-Split Transformation
-----------------------------
(C) Frank-Rene Schaefer

The 'State-Split' is a procedure transforms a state machine that triggers on
some 'pure' values (e.g. Unicode Characters) into a state machine that triggers
on the code unit sequences (e.g. UTF8 Code Units) that correspond to the
original values. For example, a state transition on a Unicode Character
'0x1329D' as shown below,

        [ A ]--->( 0x1329D )---->[ B ]

is translated into a sequence of UTF16 transitions with a new intermediate
state 'i' as follows.

        [ A ]--( 0xD80C )-->[ i ]-->( 0xDE9E )-->[ B ]

This is so, since the character 0x1329D in Unicode is represented as the
sequence 0xD80C, 0xDE9E. The present algorithm exploits the fact that
translations of adjacent character result in sequences of adjacent intervals.

 .----------------------------------------------------------------------------.
 | This procedure is to be used for encodings of dynamic size, i.e. where the |
 | number of code units to represent a 'pure' value changes depending on the  |
 | value itself (e.g. UTF8, UTF16).                                           |
 '----------------------------------------------------------------------------'

PRINCIPLE:

A state transition is described by a 'trigger set' and a target state.  If an
input occurs that belongs to the 'trigger set' the state machine transits into
the specific target state. Trigger sets are composed of one ore more intervals
of adjacent values. If the encoding has some type of continuity, it can be
assumed that an interval in the pure values can be represented by a sequence of
intervals in the transformed state machine. This is, indeed true for the
encodings UTF8 and UTF16.

The algorithm below considers intervals of pure values and translates them
into interval sequences. All interval sequences of a triggger set that 
triggers to a target state are then combined into a set of state transitions.

A unicode transition from state A to state B:

         [ A ]-->(x0, x1)-->[ B ]

is translated into a chain of utf8-byte sequence transitions that might look
like this

     [ A ]-->(b0)-->[ 1 ]-->(c0,c1)-->[ B ] 
         \                             /
          `->(d1)-->[ 2 ]---(e0,e1)---' 

That means that intermediate states may be introduced to reflect the different
byte sequences that represent the original interval.

IDEAS:
    
In a simple approach one would translate each element of a interval into an
utf8-byte sequence and generate state transitions between A and B.  Such an
approach, however, produces a huge computational overhead and charges the later
Hopcroft Minimization with a huge state machine.

To avoid such an hughe computational effort, the Hopcroft Minimzation can be
prepared on the basis of transition intervals. 
    
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

(1) The original interval translated into a list of interval sequence
    that represent the values in the target encoding.

(2) The interval sequences are plugged in between the state A and B
    of the state machine.
"""
from   quex.engine.state_machine.core                import StateMachine
import quex.engine.state_machine.transformation.base as     base
from   quex.engine.misc.interval_handling            import NumberSet, \
                                                            Interval

from   quex.engine.misc.tools import flatten_list_of_lists

class EncodingTrafoByFunction(base.EncodingTrafo):
    """Transformation that takes a lexatom and produces a lexatom sequence.
    """
    def __init__(self, Name):
        base.EncodingTrafo.__init__(self, Name,
                                    self.get_unicode_range(), 
                                    self.get_code_unit_range())

    def do_transition(self, sm, FromSi, from_target_map, ToSi, beautifier):
        """RETURNS: [0] True if complete, False else.
                    [1] True if orphan states possibly generated, False else.
        """
        number_set = from_target_map[ToSi]

        # Check whether a modification is necessary
        if number_set.supremum() <= self.UnchangedRange: 
            return True, False

        # Cut out any forbiddin range. Assume, that is has been checked
        # before, or is tolerated to be omitted.
        self.prune(number_set)

        transformed_interval_sequence_list = self.do_NumberSet(number_set)

        # First, remove the original transition.
        del from_target_map[ToSi]

        # Second, enter the new transitions.
        _plug_interval_sequences(sm, FromSi, ToSi, 
                                 transformed_interval_sequence_list, beautifier)
        return True, False

    def do_NumberSet(self, NSet):
        """RETURNS: List of interval sequences that implement the number set.
        """
        return flatten_list_of_lists(
            self.get_interval_sequences(interval)
            for interval in NSet.get_intervals(PromiseToTreatWellF=True)
        )

    def variable_character_sizes_f(self):
        return True

    def lexatom_n_per_character_in_state_machine(self, SM):
        lexatom_n = None
        for state in SM.states.itervalues():
            for number_set in state.target_map.get_map().itervalues():
                candidate_lexatom_n = self.lexatom_n_per_character(number_set)
                if   candidate_lexatom_n is None:      return None
                elif lexatom_n is None:                lexatom_n = candidate_lexatom_n
                elif lexatom_n != candidate_lexatom_n: return None
        return lexatom_n

    def hopcroft_minimization_always_makes_sense(self): 
        return True

def _plug_interval_sequences(sm, BeginIndex, EndIndex, IntervalSequenceList, beautifier):
    sub_sm = StateMachine.from_interval_sequences(IntervalSequenceList)
    # sub_sm = _plug_encoding_error_detectors(sub_sm)
    sub_sm = beautifier.do(sub_sm)

    # The 'End State' is the state where there are no further transitions.
    new_end_si = None
    for state_index, state in sub_sm.states.iteritems():
        if state.target_map.is_empty(): new_end_si = state_index
    assert new_end_si is not None

    # Mount the states inside the state machine
    sm.mount_absorbed_states_between(BeginIndex, EndIndex, 
                                     sub_sm.states, sub_sm.init_state_index, new_end_si)

error_lexatom0 = NumberSet([
    Interval(0x00, 0x7F+1),
    Interval(0xC0, 0xDF+1),
    Interval(0xE0, 0xEF+1),
    Interval(0xF0, 0xF7+1),
    Interval(0xF8, 0xFB+1),
    Interval(0xFC, 0xFD+1),
])

error_lexatomN = NumberSet(Interval(0x80, 0xBF+1))

def _plug_encoding_error_detectors(sm):
    """Adorn states with transitions to the 'on_encoding_error' handler if the 
    input value lies beyond the limits. The state machine is an implementation
    of linear sequences of intervals. Thus, the 'byte position' can be 
    be determined by the number of transitions from the init state.

    sm = mini state machine that implements the transition sequences.

    UTF8 Encodings in binary look like the following (see 'man utf8').

        0xxxxxxx
        110xxxxx 10xxxxxx
        1110xxxx 10xxxxxx 10xxxxxx
        11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
        111110xx 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx
        1111110x 10xxxxxx 10xxxxxx 10xxxxxx 10xxxxxx 10xxx

    For UTF8, admissible values are dependent on the byte position:

        Byte[0]:    [00-7F], [C0-DF], [E0-EF], [F0-F7], [F8-FB], [FC-FD]
        Byte[>0]:   [80-BF]
    """
    # 'Byte[0]' appears at the init state
    init_tm = sm.get_init_state().target_map.get_map()
    init_tm[E_StateIndices.ON_BAD_LEXATOM] = error_lexatom0

    # 'Byte[>0]' appear all at later states
    workset = set(init_tm.iterkeys())
    done    = set()
    while workset:
        si = worklist.pop()
        tm = sm.states[si].target_map.get_map()
        tm[E_StateIndices.ON_BAD_LEXATOM] = error_lexatomN
        done_set.add(si)
        workset.update(new_si for new_si in tm.iterkeys() 
                       if new_si not in done_set)

