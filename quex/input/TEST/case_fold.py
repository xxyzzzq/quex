"""This implements the basic algorithm for caseless matching
   as described in Unicode Standard Annex #21, Section 1.3.
"""
#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.ucs_db_case_fold_parser as parser
from quex.core_engine.utf8                import map_unicode_to_utf8


if "--hwut-info" in sys.argv:
    print "Case Folding based on Unicode Database;"
    print "CHOICES: CommonUpper, CommonLower, Full, Simple, Turkish;"
    sys.exit()


def pump(LetterList):
    txt = ""
    for x in LetterList:
        if type(x) != list:
            txt += map_unicode_to_utf8(x)
        else:
            for xe in x:
                txt += map_unicode_to_utf8(xe)
        txt += ", "

    if txt != "": txt = txt[:-2]
    return txt

if sys.argv[1].find("Common") == 0:
    if "CommonLower" in sys.argv: 
        Letters = "abcdefghijklmnopqrstuvwxyz"
    elif "CommonUpper" in sys.argv:
        Letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    print "Origin:      All:       Lower:        Upper:"
    for letter in Letters:
        code = ord(letter)
        result  = letter
        result += " -->        " 
        result += pump(parser.get_fold_set(code, "C"))
        #result += " " * (24 - len(result)) 
        #result += pump(parser.get_lower_fold_set(code, "C"))
        #result += " " * (38 - len(result)) 
        #result += pump(parser.get_upper_fold_set(code, "C"))
        print result

