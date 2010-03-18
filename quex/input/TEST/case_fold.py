#! /usr/bin/env python
# vim:fileencoding=utf8 
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
    print "CHOICES: Common, Full, Simple, Turkish;"
    sys.exit()


def pump(LetterList):
    txt = ""
    LetterList.sort()
    for x in LetterList:
        if type(x) != list:
            txt += map_unicode_to_utf8(x) 
            txt += "(%04X)" % x
        else:
            for xe in x:
                txt += map_unicode_to_utf8(xe)
                txt += "(%04X)" % xe
        txt += ", "

    if txt != "": txt = txt[:-2]
    return txt

if "Common" in sys.argv:
    for letter in [u"A", u"J", u"K", u"L", u"Q", u"S", u"X", u"Y", u"Ċ", u"Ç", u"Ø", u"É", u"Ω", u"Π"]:
        code = ord(letter)
        print letter, " --> ", pump(parser.get_fold_set(code, "CSTF"))

    for letter in [u"a", u"j", u"k", u"l", u"q", u"s", u"x", u"y", u"ċ", u"ç", u"ø", u"é", u"ω", u"π"]:
        code = ord(letter)
        print letter, " --> ", pump(parser.get_fold_set(code, "CSTF"))

