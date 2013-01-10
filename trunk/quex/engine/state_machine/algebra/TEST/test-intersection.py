#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine         as regex
import quex.engine.state_machine.check.intersection as intersection
import quex.engine.state_machine.check.identity     as identity

if "--hwut-info" in sys.argv:
    print "Pattern Superset/Subset Determination"
    print "CHOICES: Easy, FalseCases, GoodCases, FalseCasesII, GoodCasesII, Misc, Pre-Post-Conditions;"
    sys.exit(0)
    
def test(A, B):
    def __core(SuperPattern, SubPattern):
        print ("A = " + SuperPattern).replace("\n", "\\n").replace("\t", "\\t")
        print ("B = " + SubPattern).replace("\n", "\\n").replace("\t", "\\t")
        super_p = regex.do(SuperPattern, {})
        sub_p   = regex.do(SubPattern, {})
        result  = intersection.do([super_p.sm, sub_p.sm])
        print "intersection = ", result
        return result
    print "---------------------------"
    x = __core(A, B)
    print
    y = __core(B, A)

    print "identity: %s" % identity.do(x, y)

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
    test('alb|albertikus', 'albert')

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
    print "##NOTE: Pre-Context 'A+' is equivalent to 'A'"
    print "##NOTE: In both cases a single 'A' is enough."
    test('A/B(C?)/', 'A+/B/')
    test('B$',  'B')
    test('^B',  'B')
