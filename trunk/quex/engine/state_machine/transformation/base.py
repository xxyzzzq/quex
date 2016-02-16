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
        for si in sm.states.keys():
            c_f, op_f = self.do_state(sm, si, beautifier)
            if not c_f: complete_f         = False
            if op_f:    orphans_possible_f = True

        if orphans_possible_f: sm.delete_orphaned_states()

        # AFTER: Whatever happend, the transitions in the state machine MUST
        #        lie in the drain_set.
        sm.assert_range(self.drain_set)

        if not sm.is_DFA_compliant(): 
            return complete_f, beautifier.do(sm)
        elif self.hopcroft_minimization_always_makes_sense():                         
            return complete_f, beautifier.do(sm, NfaToDfaF=False)
        else:                         
            return complete_f, sm

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

    def do_NumberSet(self, number_set):              assert False

    def do_sequence(self, Sequence, fh=-1):
        return flatten_list_of_lists(
            self.do_Number(x) for x in Sequence
        )

    def lexatom_n_per_character(self, CharacterSet):        assert False

    def lexatom_n_per_character_in_state_machine(self, SM): assert False

    def variable_character_sizes_f(self): 
        """By default, character sizes are fixed. In case of exception
        this virtual function has to be re-implemented by derived class.
        """
        return False

    def hopcroft_minimization_always_makes_sense(self): 
        return False

class EncodingTrafoUnicode(EncodingTrafo):
    def __init__(self, SourceSet, DrainSet):
        EncodingTrafo.__init__(self, "unicode", SourceSet, DrainSet)

    def do_state(self, sm, SI, UnusedBeatifier):
        state              = sm.states[SI]
        target_map         = state.target_map.get_map()
        complete_f         = True
        orphans_possible_f = False
        for target_index, number_set in target_map.items():
            if self.drain_set.is_superset(number_set): continue
            complete_f = False
            number_set.intersect_with(self.drain_set)
            if number_set.is_empty(): 
                del target_map[target_index]
                orphans_possible_f = True

        return complete_f, orphans_possible_f

    def do_NumberSet(self, number_set):
        transformed = self.drain_set.intersection(number_set)
        return [ 
            [ interval ]
            for interval in transformed.get_intervals(PromiseToTreatWellF=True) 
        ]

    def lexatom_n_per_character(self, CharacterSet):
        return 1 # In non-dynamic character codecs each chunk element is a character

    def lexatom_n_per_character_in_state_machine(self, SM):
        return 1

