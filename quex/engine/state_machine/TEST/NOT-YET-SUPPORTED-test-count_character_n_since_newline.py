#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine        as core
import quex.engine.state_machine.character_counter as character_counter

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Characters since Newline"
    sys.exit(0)
    
def test(TestString):
    print ("expr.  = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    sm = core.do(TestString)
    print "char-n = ", character_counter.get_character_n_since_newline(sm)

test('"\n123"')
test('"1\n23"|"A\nBC"')
test('"1\n234"|"A\nBC"')
sys.exit(0)

