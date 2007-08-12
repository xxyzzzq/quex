#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core

if "--hwut-info" in sys.argv:
    print "lonestanding characters"
    sys.exit(0)
    
def test(TestString):
    print "expression    = \"" + TestString + "\""
    print "state machine\n", core.do(TestString)

test('you(a|b)you')
test('[fb]oo-a')
test('a*(b|cd+)e+')
test('a*.b*')     # '.' == anything by newline
test('\\"\\n')
test('\\"\\[\\]\\-\\*\\+\\$\\^\\)\\(')
