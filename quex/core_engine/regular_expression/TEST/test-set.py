#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.character_set as character_set

if "--hwut-info" in sys.argv:
    print "map character *range* to state machine"
    sys.exit(0)
    
def test(TestString):
        print "expression    = \"" + TestString + "\""
        print "state machine\n", character_set.do(TestString)

test("a-z")
test("ABCDE0-9")
test("ABCD\\aE0-9")
test("A-Z\\n\\\"^CD")
