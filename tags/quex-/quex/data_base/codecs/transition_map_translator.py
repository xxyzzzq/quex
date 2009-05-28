#! /usr/bin/env python
#
# PURPOSE: Helper script to create database files that describe the mapping from
#          unicode characters to character codes of a particular encoding.
#
#    $1 Encoding name (see http://docs.python.org/library/codecs.html#encodings-and-unicode)
#
#    $2 Language(s)
#
# (C) 2009 Frank-Rene Schaefer
# ABSOLUTELY NO WARRANTY

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.frs_py.file_in                                            import open_file_or_die
from quex.core_engine.interval_handling                             import Interval
from quex.core_engine.regular_expression.snap_backslashed_character import __parse_hex_number

import codecs

def translate(CodecDB, NSet):
    """Converts the given number set according the information provided in the 
       codec database 'CodecDB'. Use function get_codec_database() in order to
       read in the codec database for a specific character coding.
    """
    interval_list = NSet.get_intervals(PromiseNotToChangeAnythingF=True)
    result        = NumberSet()
    CodecL        = len(CodecDB)

    # Assume that the CodecDB is sorted, and so is the number set.
    codec_i = 0
    for interval in interval_list:
        # Find intersecting interval
        for index in range(codec_i, CodecL): 
            codec_interval = CodecDB[index][0]
            if interval.begin > codec_interval.end: 
                codec_i += 1
                continue
            if interval.end   > codec_interval.end:
                error_message("No mapping for '%s'" % interval.get_utf8_string())

            offset = interval.begin - codec_interval.begin
            length = interval.end   - interval.begin

            # Append the new interval
            codec_target_interval_begin = CodecDB[index][1]
            # 
            result.add_interval(Interval(codec_target_interval_begin + offset,
                                         codec_target_interval_begin + length))

     return result

def get_codec_db_list():
    """
       ...
       [ CODEC_NAME  [CODEC_NAME_LIST]  [LANGUAGE_NAME_LIST] ]
       ...
    """
    file_name = os.environ["QUEX_PATH"] + "/quex/data_base/codecs/list.txt"
    fh        = open_file_or_die(file_name, "rb")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    db_list = []
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
        db_list.append(codec, aliases_list, language_list)

    return db_list

def get_distinct_codec_name_for_alias(CodecAlias):
    codec_db_list = get_codec_db_list()
    for record in codec_db_list:
        if CodecAlias in record[1] or CodecAlias == record[0]: 
            return record[0]
    return None

def get_codec_database(Codec):
    """Provides the information about the relation of character codes in a particular 
       coding to unicode character codes. It is provided in the following form:

       [ (SourceInterval0, TargetInterval0_Begin), 
         (SourceInterval1, TargetInterval1_Begin),
         (SourceInterval2, TargetInterval2_Begin), ... ]

    """
    distinct_code = get_distinct_codec_name_for_alias(Codec)
    file_name     = os.environ["QUEX_PATH"] + "/quex/data_base/codecs/%s.dat" % distinct_codec

    fh = open_file_or_die(file_name, "rb")

    # Read coding into data structure
    db = []
    try:
        for line in fh.readlines():
            if line == "" or line[0] == "#": continue
            fields = line.split()
            in_interval        = Interval(int(fields[0]), int(fields[0]) + int(fields[1]))
            out_interval_begin = int(fields[2])

            db.append((in_interval, out_interval_begin))
    except:
        error_msg("Syntax error in database file for codec '%s'." % Codec)

    return db



def __help(TargetEncoding, TargetEncodingName):
    """Writes a database file for a given TargetEncodingName. The 
       TargetEncodingName is required to name the file where the 
       data is to be stored.
    """
    encoder     = codecs.getencoder(TargetEncoding)
    prev_output = -1
    db          = []
    for input in range(0x110000):

        input_str = unichr(input)
        try:    result = encoder(input_str)[0]
        except: result = None

        if result == None:
            # '-1' stands for: 'no encoding for given unicode character'
            output = -1

        elif len(result) >= 2 and result == "\\u":
            # For compatibility with versions of python <= 2.5, convert the unicode
            # string by hand.
            output = __parse_hex_number(result[2:], len(result) - 2)

        else:
            if len(result)   == 1: output = ord(result)
            elif len(result) == 2: output = ord(result[0]) * 256 + ord(result[1])
            elif len(result) == 3: output = ord(result[0]) * 65536 + ord(result[1]) * 256 + ord(result[2])

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
        self.__db.append((interval, target_interval_begin))

    fh = open(os.environ["QUEX_PATH"] + "/quex/data_base/codecs/%s.dat" % TargetEncoding, "wb")
    fh.write("# Describes mapping from Unicode Code pointer to Character code in %s (%s)\n" \
             % (TargetEncoding, TargetEncodingName))
    fh.write("# [SourceInterval.begin] [SourceInterval.Size]  [TargetInterval.begin] (all in hexidecimal)\n")
    for i, t in db:
        fh.write("%X %X %X\n" % (i.begin, i.end - i.begin, t))
    fh.close()


        
if __name__ == "__main__":
    fh = open("list.txt")
    # FIELD SEPARATOR:  ';'
    # RECORD SEPARATOR: '\n'
    # FIELDS:           [Python Coding Name]   [Aliases]   [Languages] 
    # Aliases and Languages are separated by ','
    db_list = get_codec_db_list()
    for record in db_list:
        codec         = record[0]
        language_list = record[2]
        print language_list, "(", codec, ")"
        __help(codec, language_list)
            
