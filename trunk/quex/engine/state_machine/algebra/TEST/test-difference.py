#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine     as regex
import quex.engine.state_machine.algebra.difference as difference

if "--hwut-info" in sys.argv:
    print "Difference Operation"
    print "CHOICES: Easy, FalseCases, GoodCases, FalseCasesII, GoodCasesII, Misc;" #, Pre-Post-Conditions;"
    sys.exit(0)
    
def test(A, B):
    def __core(SuperPattern, SubPattern):
        print ("super = " + SuperPattern).replace("\n", "\\n").replace("\t", "\\t")
        print ("sub   = " + SubPattern).replace("\n", "\\n").replace("\t", "\\t")
        super_p = regex.do(SuperPattern, {}).sm
        sub_p   = regex.do(SubPattern, {}).sm
        print "result = ", difference.do(super_p, sub_p).get_string(NormalizeF=True)
    print "---------------------------"
    __core(A, B)
    print
    __core(B, A)

if "Easy" in sys.argv:

    test('[0-9]+', '0')
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
    test('alb|albertikus', 'albert')

elif "GoodCases" in sys.argv:
    test('"123"+',  '"123"')
    test('X"123"?', 'X"123"')
    test('"123"?X', '"123"X')
    test('"123"*X', '"123"X')
    test('X"123"*', 'X"123"')

elif "FalseCasesII" in sys.argv:
    test('ab("123"+)yz',       'abz')
    test('ab("123"|"ABC")yz',  'ab1B3yz')
    test('ab("123"|"ABCD")yz', 'abABCyc')

elif "GoodCasesII" in sys.argv:
    test('ab("12"+)yz',      'ab121212yz')
    test('ab("12"?)yz',      'abyz')
    test('ab("12"*)yz',      'abyz')
    test('ab("12"|"AB")?yz', 'abyz')
    test('ab("12"|"AB")?yz', 'abAByz')
    test('ab("12"|"AB")*yz', 'abyz')
    test('ab("12"|"AB")*yz', 'abAB12yz')

elif "Misc" in sys.argv:
    test('X("a"|"x"?|"e"|"g")', 'X')
    test('X("a"|"x"?|"e"|"g")', 'Xx')
    test('"a"|"x"+|"e"|"g"', 'x{4}')
    test('X("a"|"x"*|"e"|"g")', 'X')
    test('X("a"|"x"*|"e"|"g")', 'Xx{4}')

    test('ab("12"|("AB"|"XY")+)+"12"("AA"|"BB")?z', 'ab12AB12AAz')

elif "Pre-Post-Conditions":
    # with pre and post-conditions
    test('A/B',      'AB')
    test('A/B/',     'B')
    test('A/B(C?)/', 'A/B/')
    print "##NOTE: Pre-Context 'A+' is equivalent to 'A'"
    print "##NOTE: In both cases a single 'A' is enough."
    test('A/B(C?)/', 'A+/B/')
    test('B$',  'B')
    test('^B',  'B')
