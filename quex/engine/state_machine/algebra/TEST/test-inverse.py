#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine      as regex
import quex.engine.state_machine.algebra.inverse as inverse
import quex.engine.state_machine.check.identity  as identity

if "--hwut-info" in sys.argv:
    print "Inverse State Machines"
    print "CHOICES: Easy, FalseCases, GoodCases, FalseCasesII, GoodCasesII, Misc;"
    sys.exit(0)
    
def test(A_str):
    print ("A = " + A_str).replace("\n", "\\n").replace("\t", "\\t")
    a_pattern = regex.do(A_str, {})
    result_1st    = inverse.do(a_pattern.sm)
    print "1st:", result_1st
    result_2nd    = inverse.do(result_1st)
    print "2nd:", result_2nd
    print "identity(A, 2nd):", identity.do(a_pattern.sm, result_2nd)

if "Easy" in sys.argv:
    test('[0-9]+')
    test('[0-9]')
    test('12')
    test('123')
    test('123(4?)')
    test('1(2?)')
    test('"123"|"ABC"')
    test('\\n')
    test('(\\r\\n)|\\n')

elif "FalseCases" in sys.argv:
    test('"12"|"A"')
    test('[a-n]')
    test('alb|albertikus')

elif "GoodCases" in sys.argv:
    test('"123"*X')
    test('"123"+')
    test('"123"?X')
    test('"123"X')
    test('X"123"')
    test('X"123"*')
    test('X"123"?')

elif "FalseCasesII" in sys.argv:
    test('abc("123"+)xyz')
    test('abc("123"|"ABC")xyz')
    test('abc("123"|"ABCD")xyz')
    test('abc1B3xyz')
    test('abcABCxyc')
    test('abcyz')

elif "GoodCasesII" in sys.argv:
    test('abc("123"*)xyz')
    test('abc("123"+)xyz')
    test('abc("123"?)xyz')
    test('abc("123"|"ABC")*xyz')
    test('abc("123"|"ABC")?xyz')
    test('abc123123123123xyz')
    test('abcABC123xyz')
    test('abcABCxyz')
    test('abcxyz')

elif "Misc" in sys.argv:
    test('"a"|"x"+|"e"|"g"')
    test('((((((((p+)r)+i)+)n)+t)+e)+r)+')
    test('(printer|rinter|inter|nter|ter|er|r)+')
    test('X("a"|"x"*|"e"|"g")')
    test('X("a"|"x"?|"e"|"g")')
    test('abc("123"|("ABC"|"XYZ")+)+"123"("AAA"|"BBB"|"CCC")?xyz')

