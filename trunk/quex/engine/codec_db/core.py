#! /usr/bin/env python
#
# (C) 2009 Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import codecs

from quex.DEFINITIONS         import QUEX_PATH
from quex.engine.misc.file_in import get_file_content_or_die, \
                                     open_file_or_die, \
                                     open_safely, \
                                     error_msg, \
                                     verify_word_in_list, \
                                     EndOfStreamException, \
                                     read_integer, \
                                     skip_whitespace
from quex.engine.interval_handling                            import Interval, NumberSet
from quex.engine.tools                                        import typed
from quex.input.regular_expression.snap_backslashed_character import __parse_hex_number

_codec_db_path = QUEX_PATH + "/quex/engine/codec_db/database"

_codec_list_db = []
_supported_codec_list = []
_supported_codec_list_plus_aliases = []

def get_codec_list_db():
    """
       ...
       [ CODEC_NAME  [CODEC_NAME_LIST]  [LANGUAGE_NAME_LIST] ]
       ...
    """
    global _codec_list_db
    if len(_codec_list_db) != 0: return _codec_list_db

    fh = open_file_or_die(_codec_db_path + "/00-ALL.txt", "rb")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    _codec_list_db = []
    for line in fh.readlines():
        line = line.strip()
        if len(line) == 0 or line[0] == "#": continue
        fields = map(lambda x: x.strip(), line.split(";"))
        try:
            codec         = fields[0]
            aliases_list  = map(lambda x: x.strip(), fields[1].split(","))
            language_list = map(lambda x: x.strip(), fields[2].split(","))
        except:
            print "Error in line:\n%s\n" % line
        _codec_list_db.append([codec, aliases_list, language_list])

    fh.close()
    return _codec_list_db

def get_supported_codec_list(IncludeAliasesF=False):
    assert type(IncludeAliasesF) == bool

    global _supported_codec_list
    if len(_supported_codec_list) != 0: 
        if IncludeAliasesF: return _supported_codec_list_plus_aliases
        else:               return _supported_codec_list

    file_name = QUEX_PATH + "/quex/engine/codec_db/database/00-SUPPORTED.txt"
    content   = get_file_content_or_die(file_name)

    _supported_codec_list = content.split()
    _supported_codec_list.sort()
    codec_db_list = get_codec_list_db()
    for codec_name, aliases_list, dummy in codec_db_list:
        if codec_name in _supported_codec_list: 
            _supported_codec_list_plus_aliases.extend(filter(lambda x: x != "", aliases_list))
        
    _supported_codec_list_plus_aliases.sort()
    if IncludeAliasesF: return _supported_codec_list_plus_aliases
    else:               return _supported_codec_list

def get_supported_language_list(CodecName=None):
    if CodecName is None:
        result = []
        for record in get_codec_list_db():
            for language in record[2]:
                if language not in result: 
                    result.append(language)
        result.sort()
        return result
    else:
        for record in get_codec_list_db():
            if record[0] == CodecName: return record[2]
        return []

def get_codecs_for_language(Language):
    
    result = []
    for record in get_codec_list_db():
        codec = record[0]
        if codec not in get_supported_codec_list(): continue
        if Language in record[2]: 
            result.append(record[0])
    if len(result) == 0:
        verify_word_in_list(Language, get_supported_language_list(),
                "No codec found for language '%s'." % Language)
    return result

def _get_distinct_codec_name_for_alias(CodecAlias, FH=-1, LineN=None):
    """Arguments FH and LineN correspond to the arguments of error_msg."""
    assert len(CodecAlias) != 0

    for record in get_codec_list_db():
        if CodecAlias in record[1] or CodecAlias == record[0]: 
            return record[0]

    verify_word_in_list(CodecAlias, get_supported_codec_list(), 
                        "Character encoding '%s' unknown to current version of quex." % CodecAlias,
                        FH, LineN)

#______________________________________________________________________________
#
# CodecTransformationInfo(list):
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
class CodecInfo:
    def __init__(self, Name, SourceSet, DrainSet):
        self.name       = Name
        self.source_set = SourceSet
        self.drain_set  = DrainSet

    def transform(self, sm):
        return True, sm

    def transform_NumberSet(self, number_set):
        return number_set

    def transform_Number(self, number):
        return [ number_set ]

class CodecDynamicInfo(CodecInfo):
    def __init__(self, Name, ImplementingModule):
        CodecInfo.__init__(self, 
                    Name,
                    ImplementingModule.get_unicode_range(), 
                    ImplementingModule.get_codec_element_range())
        self.module = ImplementingModule

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
        return self.transform_NumberSet(NumberSet(number)).get_intervals()

    def homogeneous_chunk_n_per_character(self, SM_or_CharacterSet):
        """Consider a given state machine (pattern). If all characters involved in the 
        state machine require the same number of chunks (2 bytes) to be represented 
        this number is returned. Otherwise, 'None' is returned.

        RETURNS:   N > 0  number of chunks (2 bytes) required to represent any character 
                          in the given state machine.
                   None   characters in the state machine require different numbers of
                          chunks.
        """
        if isinstance(SM_or_CharacterSet, NumberSet):
            return self.module.homogeneous_chunk_n_per_character(SM_or_CharacterSet)
        else:
            chunk_n = None
            for state in SM_or_CharacterSet.states.itervalues():
                for number_set in state.target_map.get_map().itervalues():
                    candidate_chunk_n = self.module.homogeneous_chunk_n_per_character(number_set)
                    if   candidate_chunk_n is None:    return None
                    elif chunk_n is None:              chunk_n = candidate_chunk_n
                    elif chunk_n != candidate_chunk_n: return None
            return chunk_n

class CodecTransformationInfo(list):
    def __init__(self, Codec=None, FileName=None, ExitOnErrorF=True):
        assert Codec is not None or FileName is not None

        if FileName is not None:
            codec_name = "file:%s" % FileName
            file_name  = FileName
        else:
            codec_name = _get_distinct_codec_name_for_alias(Codec)
            file_name  = _codec_db_path + "/%s.dat" % distinct_codec

        source_set, drain_set = self.__load(file_name, ExitOnErrorF)
        CodecInfo.__init__(self, codec_name, source_set, drain_set)

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
        return self.transform_NumberSet(NumberSet(number)).get_intervals()

    def __load(self, FileName, ExitOnErrorF):
        # Read coding into data structure
        source_set = NumberSet()
        drain_set  = NumberSet()

        error_str = None
        fh        = open_file_or_die(file_name, "rb")

        try:
            while error_str is None:
                skip_whitespace(fh)
                source_begin = read_integer(fh)
                if source_begin is None:
                    error_str = "Missing integer (source interval begin) in codec file."
                    continue

                skip_whitespace(fh)
                source_size = read_integer(fh)
                if source_size is None:
                    error_str = "Missing integer (source interval size) in codec file." 
                    continue

                skip_whitespace(fh)
                target_begin = read_integer(fh)
                if target_begin is None:
                    error_str = "Missing integer (target interval begin) in codec file."
                    continue

                source_end = source_begin + source_size
                list.append(self, [source_begin, source_end, target_begin])

                source_set.add_interval(Interval(source_begin, source_end))
                drain_set.add_interval(Interval(target_begin, target_begin + source_size))

        except EndOfStreamException:
            pass

        if error_str is not None:
            error_msg(error_str, fh, DontExitF=not ExitOnErrorF)
            self.__set_invalid() # Transformation is not valid.

        return source_set, drain_set

    def __set_invalid(self):
        list.clear(self)                  
        self.source_set = None
        self.drain_set  = None

def get_supported_unicode_character_set(CodecAlias=None, FileName=None):
    """RETURNS:

       NumberSet of unicode characters which are represented in codec.
       None, if an error occurred.

       NOTE: '.source_set' is None in case an error occurred while constructing
             the CodecTransformationInfo.
    """
    return CodecTransformationInfo(CodecAlias, FileName, ExitOnErrorF=False).source_set

def __AUX_get_transformation(encoder, CharCode):
    # Returns the encoding for the given character code, 
    # plus the number of bytes which it occupies.
    input_str = eval("u'\\U%08X'" % CharCode)
    try:    
        result = encoder(input_str)[0]
    except: 
        # '-1' stands for: 'no encoding for given unicode character'
        return -1, -1

    if len(result) >= 2 and result == "\\u":
        # For compatibility with versions of python <= 2.5, convert the unicode
        # string by hand.
        n = (len(result) - 2) / 2
        return __parse_hex_number(result[2:], len(result) - 2), n

    else:
        L = len(result) 
        if   L == 1: return ord(result), 1
        elif L == 2: return ord(result[0]) * 256      + ord(result[1]), 2
        elif L == 3: return ord(result[0]) * 65536    + ord(result[1]) * 256 + ord(result[2]), 3
        elif L == 4: return ord(result[0]) * 16777216L + ord(result[0]) * 65536 + ord(result[1]) * 256 + ord(result[2]), 4
        else:
            print "Character Encoding of > 4 Bytes."
            return -1, 5

def __AUX_create_database_file(TargetEncoding, TargetEncodingName):
    """Writes a database file for a given TargetEncodingName. The 
       TargetEncodingName is required to name the file where the 
       data is to be stored.
    """
    encoder     = codecs.getencoder(TargetEncoding)
    prev_output = -1
    db          = []
    bytes_per_char = -1
    for input in range(0x110000):
        output, n = __AUX_get_transformation(encoder, input)

        if bytes_per_char == -1: 
            bytes_per_char = n
        elif n != -1 and bytes_per_char != n:
            print "# not a constant size byte format."
            return False

        # Detect discontinuity in the mapping
        if   prev_output == -1:
            if output != -1:
                input_interval        = Interval(input)
                target_interval_begin = output

        elif output != prev_output + 1:
            # If interval was valid, append it to the database
            input_interval.end    = input
            db.append((input_interval, target_interval_begin))
            # If interval ahead is valid, prepare an object for it
            if output != -1:
                input_interval        = Interval(input)
                target_interval_begin = output

        prev_output = output

    if prev_output != -1:
        input_interval.end = input
        db.append((input_interval, target_interval_begin))

    fh = open_file_or_die(_codec_db_path + "/%s.dat" % TargetEncoding, "wb")
    fh.write("// Describes mapping from Unicode Code pointer to Character code in %s (%s)\n" \
             % (TargetEncoding, TargetEncodingName))
    fh.write("// [SourceInterval.begin] [SourceInterval.Size]  [TargetInterval.begin] (all in hexidecimal)\n")
    for i, t in db:
        fh.write("0x%X %i 0x%X\n" % (i.begin, i.end - i.begin, t))
    fh.close()

    return True

if __name__ == "__main__":
    # PURPOSE: Helper script to create database files that describe the mapping from
    #          unicode characters to character codes of a particular encoding.
    fh           = open("00-ALL.txt")
    fh_supported = open("00-SUPPORTED.txt", "wb")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    db_list = get_codec_list_db()
    for record in db_list:
        codec         = record[0]
        language_list = record[2]
        print repr(language_list) + " (", codec, ")",
        if __AUX_create_database_file(codec, language_list):
            fh_supported.write("%s " % codec)
            print "[OK]"
            
