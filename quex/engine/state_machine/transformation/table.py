import quex.engine.codec_db.core as codec_db
from   quex.engine.state_machine.transformation.base import EncodingTrafo

import os

class EncodingTrafoByTable(EncodingTrafo, list):
    """Provides the information about the relation of character codes in a 
    particular coding to unicode character codes. It is provided in the 
    following form:

           # Codec Values                 Unicode Values
           [ (Source0_Begin, Source0_End, TargetInterval0_Begin), 
             (Source1_Begin, Source1_End, TargetInterval1_Begin),
             (Source2_Begin, Source2_End, TargetInterval2_Begin), 
             ... 
           ]

    """
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

    def transform(self, sm, UnusedBeatifier):
        """RETURNS: True  transformation for all states happend completely.
                    False transformation may not have transformed all elements because
                          the target codec does not cover them.
        """
        complete_f         = True
        orphans_possible_f = False
        for si in sm.states.keys():
            c_f, op_f = self.__transform_state(sm, si, UnusedBeatifier)
            if not c_f: complete_f         = False
            if op_f:    orphans_possible_f = True

        # If some targets have been deleted from target maps, then a orphan state 
        # deletion operation is necessary.
        if orphans_possible_f:
            sm.delete_orphaned_states()

        return complete_f, sm

    def __transform_state(self, sm, SI, UnusedBeatifier):
        state              = sm.states[SI]
        target_map         = state.target_map.get_map()
        complete_f         = True
        orphans_possible_f = False
        L = len(state.target_map.get_map())
        if not state.target_map.transform(self):
            complete_f = False
            if L != len(state.target_map.get_map()):
                orphans_possible_f = True

        return complete_f, orphans_possible_f

    def transform_NumberSet(self, number_set):
        return number_set.transform(self)

    def __set_invalid(self):
        list.clear(self)                  
        self.source_set = None
        self.drain_set  = None

