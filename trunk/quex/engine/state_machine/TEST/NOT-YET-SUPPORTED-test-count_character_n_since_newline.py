#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine as core
import quex.core_engine.state_machine.character_counter as counter

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Characters since Newline"
    sys.exit(0)
    
def test(TestString):
    print ("expr.  = " + TestString).replace("\n", "\\n").replace("\t", "\\t")
    sm = core.do(TestString)
    print "char-n = ", counter.get_character_n_since_newline(sm)

test('"\n123"')
test('"1\n23"|"A\nBC"')
test('"1\n234"|"A\nBC"')
sys.exit(0)

test('"123"+')
test('"123"?')
test('"123"*')

test('abc("123"+)')
test('abc("123"?)')
test('abc("123"*)')

test('abc("123"+)xyz')
test('abc("123"?)xyz')
test('abc("123"*)xyz')

test('abc("123"|"ABC")xyz')
test('abc("123"|"ABCD")xyz')
test('abc("123"|"ABC")+xyz')
test('abc("123"|"ABC")?xyz')
test('abc("123"|"ABC")*xyz')

test('"a"|"c"|"e"|"g"')
test('"a"|"x"?|"e"|"g"')
test('"a"|"x"+|"e"|"g"')
test('"a"|"x"*|"e"|"g"')

test('abc("123"|("ABC"|"XYZ"))"123"("AAA"|"BBB"|"CCC")xyz')
test('abc("123"|("ABCD"|"XYZ"))"123"("AAA"|"BBB"|"CCC")xyz')

# with pre and post-conditions
test('"123"/"Z"')
test('"123"+/"Z"')
test('("123"|"ABC")/"Z"')
test('"123"/"ABC"|"XYZ"')
test('"123"/"ABC"|"X"*')
test('"123"/"ABC"|"X"?')
test('"123"/"ABC"|""')
test('"123"/"XYZ"+')
