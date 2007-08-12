#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core

if "--hwut-info" in sys.argv:
    print "simple repeated expressions"
    sys.exit(0)

def test(TestString):
    print "___________________________________________________________________________"
    print "expression    = \"" + TestString + "\""
    print "state machine\n", core.do(TestString)


test("[a-z]")
test('[a-z]+')
test('[a-z]*')
test('[a-z]?')
test('[a-z]{2,5}')
test('[a-z]{3,}')
test('[a-z]{4}')
test('"You"{3}')
test('"You"*')
test('"You"+')
test('"You"?')
test('a+(b|c)*t')
