#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from StringIO import StringIO

import quex.core_engine.regular_expression.traditional_character_set as character_set
from   quex.core_engine.state_machine.core import StateMachine

if "--hwut-info" in sys.argv:
    print "Basics: Map character *range* to state machine"
    sys.exit(0)
    
def test(TestString):
    print "expression    = \"" + TestString + "\""
    sm = StateMachine()
    trigger_set = character_set.do(StringIO(TestString + "]"))
    sm.add_transition(sm.init_state_index, trigger_set, AcceptanceF=True)
    print "state machine\n", sm 

test("a-z")
test("ABCDE0-9")
test("ABCD\\aE0-9")
test("A-Z\\n\\\"^CD")
test("^a-z")
test("^a")
test("^ \\n")
