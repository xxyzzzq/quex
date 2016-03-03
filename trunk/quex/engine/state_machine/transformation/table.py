import quex.engine.codec_db.core as codec_db
from   quex.engine.state_machine.transformation.base import EncodingTrafo

from   quex.blackboard import setup as Setup
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

        self.BadLexatomSet = drain_set.complement(Setup.buffer_codec.lexatom_range)

    def do_transition(self, sm, FromSi, from_target_map, ToSi, beautifier):
        """RETURNS: [0] True if complete, False else.
                    [1] True if orphan states possibly generated, False else.
        """
        number_set = from_target_map[ToSi]

        if number_set.transform(self): 
            assert not number_set.is_empty()
            return True, False

        if self.BadLexatomSet:
            bad_lexatom_state_index = sm.access_bad_lexatom_state()
            from_target_map[bad_lexatom_state_index] = self.BadLexatomSet

        if number_set.is_empty(): 
            del from_target_map[ToSi]
            return False, True
        else:
            return False, False

    def do_NumberSet(self, number_set):
        """RETURNS: List of interval sequences that implement the number set.
        """
        transformed = number_set.transform(self)
        return [ 
            [ interval ]
            for interval in transformed.get_intervals(PromiseToTreatWellF=True) 
        ]

    def __set_invalid(self):
        list.clear(self)                  
        self.source_set = None
        self.drain_set  = None

