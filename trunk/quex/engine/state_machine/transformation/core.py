# (C) Frank-Rene Schaefer
from   quex.engine.misc.interval_handling import NumberSet, Interval
from   quex.engine.misc.tools             import typed, \
                                                 flatten_list_of_lists
import quex.engine.codec_db.core          as     codec_db


import os

class EncodingTrafo:
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
        complete_f, sm_out = self.transform(SmIn)

        # AFTER: Whatever happend, the transitions in the state machine MUST
        #        lie in the drain_set.
        sm_out.assert_range(self.drain_set)

        if sm_out.is_DFA_compliant(): return complete_f, sm_out
        else:                         return complete_f, beautifier.do(sm_out)

    def do_sequence(self, Sequence, fh=-1):
        return flatten_list_of_lists(
            self.transform_Number(x) for x in Sequence
        )

    def transform(self, sm):                                assert False
    def transform_NumberSet(self, number_set):              assert False
    def transform_Number(self, number):                     assert False
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


    def transform(self, sm):
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

    def transform_Number(self, number):
        if self.drain_set.contains(number): return [ Interval(number) ]
        return None

    def lexatom_n_per_character(self, CharacterSet):
        return 1 # In non-dynamic character codecs each chunk element is a character

    def lexatom_n_per_character_in_state_machine(self, SM):
        return 1

class EncodingTrafoByFunction(EncodingTrafo):
    def __init__(self, Name, ImplementingModule):
        EncodingTrafo.__init__(self, Name,
                               ImplementingModule.get_unicode_range(), 
                               ImplementingModule.get_codec_element_range())
        self.module = ImplementingModule

    def variable_character_sizes_f(self):
        return True

    def transform(self, sm):
        sm = self.module.do(sm)
        return True, sm

    @typed(number_set=NumberSet)
    def transform_NumberSet(self, number_set):
        result = self.module.do_set(number_set)
        assert result is not None, \
               "Operation 'number set transformation' failed.\n" + \
               "The given number set results in a state sequence not a single transition."
        return result

    def transform_Number(self, number):
        result = self.transform_NumberSet(NumberSet(number))
        if result is None: return None
        else:              return result.get_intervals(PromiseToTreatWellF=True)

    def lexatom_n_per_character(self, CharacterSet):
        """Consider a given state machine (pattern). If all characters involved in the 
        state machine require the same number of chunks (2 bytes) to be represented 
        this number is returned. Otherwise, 'None' is returned.

        RETURNS:   N > 0  number of chunks (2 bytes) required to represent any character 
                          in the given state machine.
                   None   characters in the state machine require different numbers of
                          chunks.
        """
        return self.module.lexatom_n_per_character(CharacterSet)

    def lexatom_n_per_character_in_state_machine(self, SM):
        chunk_n = None
        for state in SM.states.itervalues():
            for number_set in state.target_map.get_map().itervalues():
                candidate_chunk_n = self.module.lexatom_n_per_character(number_set)
                if   candidate_chunk_n is None:    return None
                elif chunk_n is None:              chunk_n = candidate_chunk_n
                elif chunk_n != candidate_chunk_n: return None
        return chunk_n

#______________________________________________________________________________
#
# EncodingTrafoByTable(list):
#
# Provides the information about the relation of character codes in a particular 
# coding to unicode character codes. It is provided in the following form:
#
#   # Codec Values                 Unicode Values
#   [ (Source0_Begin, Source0_End, TargetInterval0_Begin), 
#     (Source1_Begin, Source1_End, TargetInterval1_Begin),
#     (Source2_Begin, Source2_End, TargetInterval2_Begin), 
#     ... 
#   ]
#
# .name           = Name of the codec.
# .file_name      = Name of file where the codec was taken from.
# .source_set     = NumberSet of unicode code points which have a representation 
#                   the given codec.
# .drain_set      = NumberSet of available code points in the given codec.
#
# NOTE: If the content of the file was not a valid codec transformation info,
#       then the following holds:
#
#       .source_set = .drain_set = None
#______________________________________________________________________________
class EncodingTrafoByTable(EncodingTrafo, list):
    def __init__(self, Codec=None, FileName=None, ExitOnErrorF=True):
        assert Codec is not None or FileName is not None

        if FileName is not None:
            file_name  = os.path.basename(FileName)
            file_name, dumped_ext = os.path.splitext(file_name)
            codec_name = file_name.replace(" ", "_").replace("\t", "_").replace("\n", "_")
            file_name  = FileName
        else:
            codec_name, \
            file_name   = codec_db.get_file_name_for_codec_alias(Codec)

        source_set, drain_set = codec_db.load(self, file_name, ExitOnErrorF)
        EncodingTrafo.__init__(self, codec_name, source_set, drain_set)

    def transform(self, sm):
        """RETURNS: True  transformation for all states happend completely.
                    False transformation may not have transformed all elements because
                          the target codec does not cover them.
        """
        complete_f         = True
        orphans_possible_f = False
        for state in sm.states.itervalues():
            L = len(state.target_map.get_map())
            if not state.target_map.transform(self):
                complete_f = False
                if L != len(state.target_map.get_map()):
                    orphans_possible_f = True

        # If some targets have been deleted from target maps, then a orphan state 
        # deletion operation is necessary.
        if orphans_possible_f:
            sm.delete_orphaned_states()

        return complete_f, sm

    def transform_NumberSet(self, number_set):
        return number_set.transform(self)

    def transform_Number(self, number):
        result = self.transform_NumberSet(NumberSet(number)).get_intervals()
        if result is None: return None
        else:              return result.get_intervals(PromiseToTreatWellF=True)

    def __set_invalid(self):
        list.clear(self)                  
        self.source_set = None
        self.drain_set  = None

