#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.snap_backslashed_character as snap

if "--hwut-info" in sys.argv:
    print "Backslashed Characters: General"
    # print "CHOICES: ALL, REDUCED"
    sys.exit(0)


def test(Title, TestString):
    print Title + ":"
    print "    characters      = \"" + TestString + "\""

    result_list = []
    i = 0; L = len(TestString)
    while i < L - 1:
        letter = TestString[i]
        assert letter == "\\" 
        code, i = snap.do(TestString, i)
        result_list.append("%04X" % code)
        if i == -1: break
    
    print "    character codes = " + repr(result_list) 



test("Hex Numbers I",   "\\xA\\xAB")
test("Hex Numbers II",  "\\X1\\X12\\X123\\X1234")
test("Hex Numbers III", "\\UA\\UAB\\UABC\\UABCD\\UABCDE\\U11A001")
test("Octal Numbers",   "\\1\\01\\20\\100")
test("ANSI-C 'Bells'",  "\\a\\b\\f\\n\\r\\t\\v")
test("Control Characters I", '\\\\\\"\\+\\*\\?\\/\\|\\$') 
test("Control Characters II", '\\^\\-\\[\\]\\(\\{\\}')


