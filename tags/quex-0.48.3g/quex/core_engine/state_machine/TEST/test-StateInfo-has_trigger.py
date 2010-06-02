#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core         as core
import quex.core_engine.state_machine.character_counter as counter

if "--hwut-info" in sys.argv:
    print "Trigger Set Check: Has Trigger "
    sys.exit(0)
    
def test(TestString, StartCharacterList):
    print "____________________________________________________________________"
    print "expr.   = " + TestString.replace("\n", "\\n").replace("\t", "\\t")
    sm = core.do(TestString, {}, -1)
    print "start   = ", map(lambda char: char.replace("\t", "\\t"), StartCharacterList)
    code_list = map(lambda char: ord(char), StartCharacterList)
    print "verdict = ", repr(sm.get_init_state().transitions().has_one_of_triggers(code_list))

test('[0-9]+', ['2', 'A'])
test('[0-9]+', ['2', '5'])
test('" 123"', [' '])
test('"\t123"', [' ', '\t'])

test('[0-9]+', ['C', 'A'])
test('[0-8]+', ['Q', '9'])
test('"\t123"', [' '])
test('"123"', [' ', '\t'])
