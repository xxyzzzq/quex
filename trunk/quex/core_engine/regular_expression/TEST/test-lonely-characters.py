#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core
import quex.core_engine.state_machine.index     as state_machine_index
from quex.input.setup import setup as Setup
Setup.buffer_limit_code = 0
Setup.path_limit_code   = 0
 
if "--hwut-info" in sys.argv:
    print "Basics: Lonestanding characters"
    sys.exit(0)
    
def test(TestString):
    # state_machine_index.clear()
    print "expression    = \"" + TestString + "\""
    print "state machine\n", core.do(TestString, {})

test('you(a|b)you')
test('[fb]oo-a')
test('a*(b|cd+)e+')
test('a*.b*')     # '.' == anything by newline
test('\\"\\n')
test('\\"\\[\\]\\-\\*\\+\\$\\^\\)\\(')

print "## NOTE: The 'c' has to be ignored, because it comes after the lonestanding space"
test('(a|b) c')
print "## NOTE: The 'c' has to be ignored, because it comes after the lonestanding space"
test('(a|b)\nc')
print "## NOTE: The '=> TKN_IF' has to be ignored, because it comes after the lonestanding space"
test('if         => TKN_IF')
test('\\n')
