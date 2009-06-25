#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.regular_expression.core as regex
import quex.core_engine.state_machine.subset    as subset

if "--hwut-info" in sys.argv:
    print "Predetermined Character Count: Characters"
    print "CHOICES: Easy;"
    sys.exit(0)
    
def test(SuperPattern, SubPattern):
    print ("super = " + SuperPattern).replace("\n", "\\n").replace("\t", "\\t")
    print ("sub   = " + SubPattern).replace("\n", "\\n").replace("\t", "\\t")
    super_sm = regex.do(SuperPattern, {}, -1)
    sub_sm   = regex.do(SubPattern, {}, -1)
    print "claim  = ", subset.do(sm)

if "Easy" in sys.argv:
    test('[0-9]+')
    test('"123"')
    test('"123"|"ABC"')
    test('"1234"|"ABC"')
else:
    test('"123"+')
    test('X"123"?')
    test('"123"?X')
    test('"123"*X')
    test('X"123"*')

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
    test('X("a"|"x"?|"e"|"g")')
    test('"a"|"x"+|"e"|"g"')
    test('X("a"|"x"*|"e"|"g")')

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
