#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
from quex.blackboard import setup as Setup
Setup.buffer_limit_code = -1
Setup.path_limit_code   = -1

if "--hwut-info" in sys.argv:
    print "Conditional Analysis: post conditions"
    sys.exit(0)
    
def test(TestString):
    print "-------------------------------------------------------------------"
    print "expression    = \"" + TestString + "\""
    sm = core.do(TestString, {}).sm
    print "state machine\n", sm 

test('"a"/";"')
test('(a|z)/c')
test('"aac"|"bad"/"z"|congo')
# test('"aac"|"bad"|bcad')
# test("you[a-b]|[a-e]|[g-m]you")    
# test("a(a|b)*")
