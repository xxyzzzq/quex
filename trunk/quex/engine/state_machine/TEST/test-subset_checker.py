#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine      as regex
import quex.core_engine.state_machine.subset_checker as subset_checker

if "--hwut-info" in sys.argv:
    print "Pattern Subset Determination"
    print "CHOICES: Easy, FalseCases, GoodCases, FalseCasesII, GoodCasesII, Misc, Pre-Post-Conditions;"
    sys.exit(0)
    
def test(A, B):
    def __core(SuperPattern, SubPattern):
        print ("super = " + SuperPattern).replace("\n", "\\n").replace("\t", "\\t")
        print ("sub   = " + SubPattern).replace("\n", "\\n").replace("\t", "\\t")
        super_sm = regex.do(SuperPattern, {})
        sub_sm   = regex.do(SubPattern, {})
        print "claim = ", subset_checker.do(super_sm, sub_sm)
    print "---------------------------"
    __core(A, B)
    print
    __core(B, A)

if "Easy" in sys.argv:
    test('[0-9]+', '[0-9]')
    test('123', '123(4?)')
    test('12', '1(2?)')
    test('1', '1(2?)')
    test('"123"|"ABC"', '"123"')
    test('\\n', '(\\r\\n)|\\n')

elif "FalseCases" in sys.argv:
    test('[a-n]', '[m-z]')
    test('"1234"|"ABC"', '"123"')
    test('"12"|"A"', '"1"')
    test('12', '1')
    test('"1BAC"|"1BBC"', '"1ABC"')

elif "GoodCases" in sys.argv:
    test('"123"+',  '"123"')
    test('X"123"?', 'X"123"')
    test('"123"?X', '"123"X')
    test('"123"*X', '"123"X')
    test('X"123"*', 'X"123"')

elif "FalseCasesII" in sys.argv:
    test('abc("123"+)xyz',       'abcyz')
    test('abc("123"|"ABC")xyz',  'abc1B3xyz')
    test('abc("123"|"ABCD")xyz', 'abcABCxyc')

elif "GoodCasesII" in sys.argv:
    test('abc("123"+)xyz', 'abc123123123123xyz')
    test('abc("123"?)xyz', 'abcxyz')
    test('abc("123"*)xyz', 'abcxyz')
    test('abc("123"|"ABC")?xyz', 'abcxyz')
    test('abc("123"|"ABC")?xyz', 'abcABCxyz')
    test('abc("123"|"ABC")*xyz', 'abcxyz')
    test('abc("123"|"ABC")*xyz', 'abcABC123xyz')

elif "Misc" in sys.argv:
    test('X("a"|"x"?|"e"|"g")', 'X')
    test('X("a"|"x"?|"e"|"g")', 'Xx')
    test('"a"|"x"+|"e"|"g"', 'x{20}')
    test('X("a"|"x"*|"e"|"g")', 'X')
    test('X("a"|"x"*|"e"|"g")', 'Xx{20}')

    test('abc("123"|("ABC"|"XYZ")+)+"123"("AAA"|"BBB"|"CCC")?xyz', 'abc123ABC123AAAxyz')

elif "Pre-Post-Conditions":
    # with pre and post-conditions
    test('A/B',      'AB')
    test('A/B/',     'B')
    test('A/B(C?)/', 'A/B/')
    test('A/B(C?)/', 'A+/B/')
    test('B$',  'B')
    test('^B',  'B')
