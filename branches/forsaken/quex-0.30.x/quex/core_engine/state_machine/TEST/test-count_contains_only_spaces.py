#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core         as core
import quex.core_engine.state_machine.character_counter as counter

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Contains only Spaces"
    sys.exit(0)
    
def test(TestString):
    print ("expr.  = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    sm = core.do(TestString, {}, -1)
    print "result = ", counter.contains_only_spaces(sm)

test('" "+')
test('[ \t]')
test('"    "[ \t]')
test('("    ")|([ \t])')
test('" "{4, 10}|(" "+)')

