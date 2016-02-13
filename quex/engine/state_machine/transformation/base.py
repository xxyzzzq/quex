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

    def do_state_machine(self, SmIn, beautifier):
        """Transforms a given state machine from 'Unicode Driven' to another
           character encoding type.
        
           RETURNS: 
           [0] Transformation complete (True->yes, False->not all transformed)
           [1] Transformed state machine. It may be the same as it was 
               before if there was no transformation actually.

           It is ensured that the result of this function is a DFA compliant
           state machine.
        """
        if SmIn is None: return True, None
        assert SmIn.is_DFA_compliant()

        # BEFORE: Forgive characters not in source range. What comes out is 
        #         important. It is checked in 'transform()' of the Pattern.
        complete_f, sm_out = self.transform(SmIn, beautifier)

        # AFTER: Whatever happend, the transitions in the state machine MUST
        #        lie in the drain_set.
        sm_out.assert_range(self.drain_set)

        if sm_out.is_DFA_compliant(): return complete_f, sm_out
        else:                         return complete_f, beautifier.do(sm_out)

    def do_sequence(self, Sequence, fh=-1):
        return flatten_list_of_lists(
            self.transform_Number(x) for x in Sequence
        )

    def transform_Number(self, number):
        result = self.transform_NumberSet(NumberSet(number))
        if result is None: return None
        else:              return result.get_intervals(PromiseToTreatWellF=True)

    def transform(self, sm, beautifier):                    assert False
    def transform_NumberSet(self, number_set):              assert False
    def lexatom_n_per_character(self, CharacterSet):        assert False

    def lexatom_n_per_character_in_state_machine(self, SM): assert False

    def variable_character_sizes_f(self): 
        """By default, character sizes are fixed. In case of exception
        this virtual function has to be re-implemented by derived class.
        """
        return False

class EncodingTrafoUnicode(EncodingTrafo):
    def __init__(self, SourceSet, DrainSet):
        EncodingTrafo.__init__(self, "unicode", SourceSet, DrainSet)

    def transform(self, sm, UnusedBeatifier):
        """Cut any number that is not in drain_set from the transition trigger
        sets. Possible orphaned states are deleted.
        """
        complete_f         = True
        orphans_possible_f = False
        for state in sm.states.itervalues():
            target_map = state.target_map.get_map()
            for target_index, number_set in target_map.items():
                if self.drain_set.is_superset(number_set): continue
                complete_f = False
                number_set.intersect_with(self.drain_set)
                if number_set.is_empty(): 
                    del target_map[target_index]
                    orphans_possible_f = True

        if orphans_possible_f:
            sm.delete_orphaned_states()

        return complete_f, sm

    def transform_NumberSet(self, number_set):
        return self.drain_set.intersection(number_set)

    def lexatom_n_per_character(self, CharacterSet):
        return 1 # In non-dynamic character codecs each chunk element is a character

    def lexatom_n_per_character_in_state_machine(self, SM):
        return 1

