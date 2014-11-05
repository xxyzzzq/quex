#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as core

if "--hwut-info" in sys.argv:
    print "Combination: Alternative Expressions"
    sys.exit(0)
    
def test(TestString):
    print "expression    = \"" + TestString + "\""
    print "state machine\n", core.do(TestString, {}, -1)

test('"a"|"c"|"e"|"g"')
test('"ac"|"bd"')
test('"aac"|"bad"')
test('"aac"|"bad"|bcad')
test("you[a-b]|[a-e]|[g-m]you")    
test("a(a|b)*")
test("[: [0-9] :]z")
