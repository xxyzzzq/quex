#! /usr/bin/env python
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
from quex.core_engine.interval_handling          import Interval
from quex.core_engine.regular_expression.snap_backslashed_character import __parse_hex_number

import codecs

def do(TargetEncoding, TargetEncodingName):
    """Creates a list of tuples:

       [ (SourceInterval, TargetInterval_Begin), ... ]

       where the numerical intervals are sorted, starting from the interval
       at position '0' with increasing border values. Use the function
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

    fh = open(os.environ["QUEX_PATH"] + "/quex/database/codecs/%s.dat" % TargetEncoding, "wb")
    fh.write("# Describes mapping from Unicode Code pointer to Character code in %s (%s)\n" \
             % (TargetEncoding, TargetEncodingName))
    fh.write("# [SourceInterval.begin] [SourceInterval.Size]  [TargetInterval.begin]\n")
    for i, t in db:
        print i.begin, i.end - i.begin, t
    fh.close()

        
if __name__ == "__main__":
    # x = Translator("950")
    # x = do("arabic")
    if len(sys.argv) != 3:
        print "This script requires exactly 2 arguments:"
        print "   $1 encoding name (see http://docs.python.org/library/codecs.html#encodings-and-unicode)\n"
        print "   $2 Language(s)"
        sys.exit()
    do(sys.argv[1], sys.argv[2])
            
            




