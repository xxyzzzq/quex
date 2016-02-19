from   quex.engine.misc.interval_handling import NumberSet
from   quex.engine.misc.tools             import flatten_list_of_lists

class EncodingTrafo:
    """Maintains information about a encoding transformation and functions that
    transform numbers and state machines from the 'pure' encoding to a target
    encoding.

        .name       = Name of the codec.
        .source_set = NumberSet of unicode code points which have a representation 
                      the given codec.
        .drain_set  = NumberSet of available code points in the given codec.
    """
    def __init__(self, Name, SourceSet, DrainSet):
        self.name       = Name
        self.source_set = SourceSet
        self.drain_set  = DrainSet

    def do_state_machine(self, sm, beautifier):
        """Transforms a given state machine from 'Unicode Driven' to another
           character encoding type.
        
           RETURNS: 
           [0] Transformation complete (True->yes, False->not all transformed)
           [1] Transformed state machine. It may be the same as it was 
               before if there was no transformation actually.

           It is ensured that the result of this function is a DFA compliant
           state machine.
        """
        if sm is None: return True, None
        assert sm.is_DFA_compliant()

        complete_f         = True
        orphans_possible_f = False
        for from_si, state in sm.states.items():
            target_map = state.target_map.get_map()
            for to_si in target_map.keys():
                c_f, op_f = self.do_transition(sm, from_si, target_map, to_si, 
                                               beautifier)
                complete_f         &= c_f
                orphans_possible_f |= op_f

        if orphans_possible_f: sm.delete_orphaned_states()

        # AFTER: Whatever happend, the transitions in the state machine MUST
        #        lie in the drain_set.
        # sm.assert_range(self.drain_set)

        if not sm.is_DFA_compliant(): 
            return complete_f, beautifier.do(sm)
        elif self.hopcroft_minimization_always_makes_sense():                         
            return complete_f, beautifier.do(sm, NfaToDfaF=False)
        else:                         
            return complete_f, sm

    def do_sequence(self, Sequence, fh=-1):
        return flatten_list_of_lists(
            self.do_Number(x) for x in Sequence
        )

    def do_Number(self, number):
        """RETURNS: A interval sequence that implements the given number.
        """
        result = self.do_NumberSet(NumberSet(number))
        # result: list of interval sequences that implement number set.
        # number set contains only one element.
        # => one interval sequence and 
        #    the interval size must be one.
        if result is None: return None
        else:              return result[0]

    def do_NumberSet(self, number_set):              
        assert False, "Must be implemented by derived class"

    def lexatom_n_per_character(self, CharacterSet):
        return 1     # Default behavior (e.g. UTF8 differs here)

    def lexatom_n_per_character_in_state_machine(self, SM):
        return 1     # Default behavior (e.g. UTF8 differs here)

    def variable_character_sizes_f(self): 
        return False # Default behavior (e.g. UTF8 differs here)

    def hopcroft_minimization_always_makes_sense(self): 
        # Default-wise no intermediate states are generated
        # => hopcroft minimization does not make sense.
        return False
        

class EncodingTrafoUnicode(EncodingTrafo):
    def __init__(self, SourceSet, DrainSet):
        EncodingTrafo.__init__(self, "unicode", SourceSet, DrainSet)

    def do_transition(self, sm, FromSi, from_target_map, ToSi, beautifier):
        """RETURNS: [0] True if complete, False else.
                    [1] True if orphan states possibly generated, False else.
        """
        number_set = from_target_map[ToSi]

        if self.drain_set.is_superset(number_set): 
            return True, False

        number_set.intersect_with(self.drain_set)
        if number_set.is_empty(): 
            del from_target_map[ToSi]
            return False, True
        else:
            return False, False

    def do_NumberSet(self, number_set):
        transformed = self.drain_set.intersection(number_set)
        return [ 
            [ interval ]
            for interval in transformed.get_intervals(PromiseToTreatWellF=True) 
        ]

