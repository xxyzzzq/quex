#! /usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from   StringIO import StringIO
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.snap_character_string as snap_character_string

if "--hwut-info" in sys.argv:
    print "Basics: Map character *string* to state machine"
    sys.exit(0)
    
def test(TestString):
    print "expression    = \"" + TestString + "\""
    print "state machine\n", snap_character_string.do(StringIO(TestString + '"'))

test("a-z")
test("ABCDE0-9")
test("ABCD\\aE0-9")
test("A-Z\\n^CD\\\"")
test("\\\"")
test("\\\\")
test("\\\\n")
test("ÿ")
