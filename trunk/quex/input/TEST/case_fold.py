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
from   quex.core_engine.utf8              import map_unicode_to_utf8


if "--hwut-info" in sys.argv:
    print "Case Folding based on Unicode Database;"
    print "CHOICES: s_simple, m_multi, sm, s_simple_turkish, m_multi_turkish, smt;"
    sys.exit()

choice = sys.argv[1]

flags = { 
            "s_simple":         "s",
            "m_multi":          "m",
            "sm":               "sm",
            "s_simple_turkish": "st",
            "m_multi_turkish":  "mt",
            "smt":              "smt",
        }[choice]

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

    if len(txt) != 0: txt = txt[:-2]
    return txt

print "---------------------------------------------"

for letter in [u"A", u"I", u"İ", u"J", u"K", u"S", u"Ċ", u"Ø", u"É", u"Ω", u"Π"]:
    code = ord(letter)
    # result = letter + u" --> " + pump(parser.get_fold_set(code, flags)) + u"\n"
    print letter, " --> ", pump(parser.get_fold_set(code, flags))

for letter in [u"a", u"ı", u"i", u"j", u"k", u"s", u"ċ", u"ø", u"é", u"ω", u"π"]:
    code = ord(letter)
    print letter, " --> ", pump(parser.get_fold_set(code, flags))

print "---------------------------------------------"
letter_list = [ 
                u"a",
                u"ß", # LATIN SMALL LETTER SHARP S
                u"ΐ", # GREEK SMALL LETTER IOTA WITH DIALYTIKA AND TONOS
                u"ŉ", # LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
                u"İ", # LATIN CAPITAL LETTER I WITH DOT ABOVE
                u"ﬀ", # LATIN SMALL LIGATURE FF
                u"ﬃ", # LATIN SMALL LIGATURE FFI
                u"ﬗ",  # ARMENIAN SMALL LIGATURE MEN XEH
                ]
for letter in letter_list:
    code = ord(letter)
    print letter, " --> ", pump(parser.get_fold_set(code, flags))
