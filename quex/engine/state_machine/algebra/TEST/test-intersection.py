#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine         as regex
import quex.engine.state_machine.algebra.intersection as intersection
import quex.engine.state_machine.check.identity     as identity

if "--hwut-info" in sys.argv:
    print "Intersection"
    print "CHOICES: 0, 1, 2, 3, 4, 5;"
    sys.exit(0)
    
def test(A, B):
    def __core(A_str, B_str):
        print ("A = " + A_str).replace("\n", "\\n").replace("\t", "\\t")
        print ("B = " + B_str).replace("\n", "\\n").replace("\t", "\\t")
        a_pattern = regex.do(A_str, {})
        b_pattern = regex.do(B_str, {})
        result    = intersection.do([a_pattern.sm, b_pattern.sm])
        print "intersection = ", result
        return result
    print "---------------------------"
    x = __core(A, B)
    print
    y = __core(B, A)

    print "identity: %s" % identity.do(x, y)

if "0" in sys.argv:
    test('[0-9]+', '[0-9]')
    test('123', '123(4?)')
    test('12', '1(2?)')
    test('1', '1(2?)')
    test('"123"|"ABC"', '"123"')
    test('\\n', '(\\r\\n)|\\n')

elif "1" in sys.argv:
    test('[a-n]', '[m-z]')
    test('"1234"|"ABC"', '"123"')
    test('"12"|"A"', '"1"')
    test('12', '1')
    test('"1BAC"|"1BBC"', '"1ABC"')
    test('alb|albertikus', 'albert')

elif "2" in sys.argv:
    test('"123"+',  '"123"')
    test('X"123"?', 'X"123"')
    test('"123"?X', '"123"X')
    test('"123"*X', '"123"X')
    test('X"123"*', 'X"123"')

elif "3" in sys.argv:
    test('abc("123"+)xyz',       'abcyz')
    test('abc("123"|"ABC")xyz',  'abc1B3xyz')
    test('abc("123"|"ABCD")xyz', 'abcABCxyc')

elif "4" in sys.argv:
    test('abc("123"+)xyz', 'abc123123123123xyz')
    test('abc("123"?)xyz', 'abcxyz')
    test('abc("123"*)xyz', 'abcxyz')
    test('abc("123"|"ABC")?xyz', 'abcxyz')
    test('abc("123"|"ABC")?xyz', 'abcABCxyz')
    test('abc("123"|"ABC")*xyz', 'abcxyz')
    test('abc("123"|"ABC")*xyz', 'abcABC123xyz')

elif "5" in sys.argv:
    test('X("a"|"x"?|"e"|"g")', 'X')
    test('X("a"|"x"?|"e"|"g")', 'Xx')
    test('"a"|"x"+|"e"|"g"', 'x{20}')
    test('X("a"|"x"*|"e"|"g")', 'X')
    test('X("a"|"x"*|"e"|"g")', 'Xx{20}')
    test('abc("123"|("ABC"|"XYZ")+)+"123"("AAA"|"BBB"|"CCC")?xyz', 'abc123ABC123AAAxyz')
    test('((((((((p+)r)+i)+)n)+t)+e)+r)+',        'priprinter')
    test('(printer|rinter|inter|nter|ter|er|r)+', 'printerter')
    test('(printer|rinter|inter|nter|ter|er|r)+', '((((((((p+)r)+i)+)n)+t)+e)+r)+')

