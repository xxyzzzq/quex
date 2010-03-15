#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.ucs_db_case_fold_parser as parser
from quex.core_engine.utf8                import map_unicode_to_utf8


if "--hwut-info" in sys.argv:
    print "Case Folding based on Unicode Database;"
    print "CHOICES: Common, Full, Simple, Turkish;"
    sys.exit()


def pump(LetterList):
    txt = ""
    for x in LetterList:
        if type(x) == list: 
            letter = ""
            for xe in x:
                letter += map_unicode_to_utf8(xe)
        else:
            letter = map_unicode_to_utf8(x)
        txt += letter + ", "
    return txt

if "Common" in sys.argv:
    print "Origin:      All:       Lower:        Upper:"
    # for letter in "abcdefghijklmnopqrstuvwxyz":
    for letter in "s":
        code = ord(letter)
        result  = letter
        result += " -->       " 
        result += pump(parser.get_fold_set(code))
        result += " " * (30 - len(result)) 
        result += pump(parser.get_lower_fold_set(code))
        result += " " * (50 - len(result)) 
        result += pump(parser.get_upper_fold_set(code))
        print result

