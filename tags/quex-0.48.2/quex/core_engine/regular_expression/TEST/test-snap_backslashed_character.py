#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from StringIO import StringIO

import quex.core_engine.regular_expression.snap_backslashed_character as snap

if "--hwut-info" in sys.argv:
    print "Backslashed Characters: General"
    # print "CHOICES: ALL, REDUCED"
    sys.exit(0)


def test(Title, TestString):
    print Title + ":"
    print "    characters      = \"" + TestString + "\""

    result_list = []
    sh = StringIO(TestString)
    while 1 + 1 == 2:
        letter = sh.read(1)
        if letter == "": break
        if letter != "\\":
            print "[end of sequence]"
            break
        code = snap.do(sh)
        result_list.append("%04X" % code)
    
    print "    character codes = " + repr(result_list) 

test("Hex Numbers I",         "\\xA\\xAB")
test("Hex Numbers II",        "\\X1\\X12\\X123\\X1234")
test("Hex Numbers III",       "\\UA\\UAB\\UABC\\UABCD\\UABCDE\\U11A001")
test("Hex Numbers IV",        "\\x0\\X0\\U0")
test("Hex Numbers V a",       "\\x041")
test("Hex Numbers V b",       "\\X00041")
test("Hex Numbers V c",       "\\U0000041")
test("Octal Numbers",         "\\1\\01\\20\\100")
test("ANSI-C 'Bells'",        "\\a\\b\\f\\n\\r\\t\\v")
test("Control Characters I",  '\\\\\\"\\+\\*\\?\\/\\|\\$') 
test("Control Characters II", '\\^\\-\\[\\]\\(\\{\\}')


