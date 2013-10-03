#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine             as regex
import quex.engine.state_machine.algebra.complement_end as complement_end
import quex.engine.state_machine.algebra.union          as union
import quex.engine.state_machine.algebra.intersection   as intersection
import quex.engine.state_machine.check.special          as special
import quex.engine.state_machine.check.identity         as identity
import quex.engine.state_machine.check.superset         as superset
import quex.engine.state_machine.algorithm.beautifier   as beautifier

if "--hwut-info" in sys.argv:
    print "Complement End: Cut patterns from P that end with Q."
    print "CHOICES: 0, 1, 2, 3, 4, 5;"
    sys.exit(0)

def clean(SM):
    result = beautifier.do(SM)
    result.clean_up()
    return result
    
def test(A, B):
    def __core(Original, Cutter):
        print ("Original = " + Original).replace("\n", "\\n").replace("\t", "\\t")
        print ("Cutter   = " + Cutter).replace("\n", "\\n").replace("\t", "\\t")
        orig   = regex.do(Original, {}).sm
        cutter = regex.do(Cutter, {}).sm
        #print orig.get_string(NormalizeF=False)
        #print cutter.get_string(NormalizeF=False)
        result = clean(complement_end.do(orig, cutter))
        print
        if not special.is_none(result):
            print "superset(Original, result):           %s" % superset.do(orig, result)
        if not special.is_none(result):
            tmp = clean(intersection.do([cutter, result]))
            print "intersection(Cutter, result) is None: %s" % special.is_none(tmp)
        tmp = clean(union.do([orig, result]))
        print "union(Original, result) == Original:  %s" % identity.do(tmp, orig)
        print
        print "result = ", result.get_string(NormalizeF=True)

    print "---------------------------"
    __core(A, B)
    print
    __core(B, A)
    #sys.exit()

#test('"1BAC"|"1BBC"', '"1ABC"')

if "0" in sys.argv:
    test('[0-9]+',    '[0-9]')
    test('[0-9]+',    '0')
    test('[0-9]+',    '01')
    test('[0-9]{2,}', '01')
    test('123',       '123(4?)')
    test('12',        '1(2?)')
    test('1',         '1(2?)')
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
    test('ab("12"+)yz',      'abz')
    test('ab("12"|"AB")yz',  'ab1B3yz')
    test('ab("12"|"ABD")yz', 'abAByc')

elif "4" in sys.argv:
    test('ab("12"+)yz', 'ab1212yz')
    test('ab("12"?)yz', 'abyz')
    test('ab("12"*)yz', 'abyz')
    test('ab("12"|"AB")?yz', 'abyz')
    test('ab("12"|"AB")?yz', 'abAByz')
    test('ab("12"|"AB")*yz', 'abyz')
    test('ab("12"|"AB")*yz', 'abAB12yz')

elif "5" in sys.argv:
    test('X("a"|"x"?|"e"|"g")', 'X')
    test('X("a"|"x"?|"e"|"g")', 'Xx')
    test('"a"|"x"+|"e"|"g"',    'x{5}')
    test('X("a"|"x"*|"e"|"g")', 'X')
    test('X("a"|"x"*|"e"|"g")', 'Xx{5}')
    # test('abc("123"|("ABC"|"XYZ")+)+"123"("AAA"|"BBB"|"CCC")?xyz', 'abc123ABC123AAAxyz')
    test('ab("12"|("AB"|"XY")+)+"12"("AA"|"BB"|"CC")?yz', 'ab12AB12AAyz')
    test('(((a+)b)+c)+', 'abcbc')
    test('(pri|ri|i)+',  'priri')
    test('(pri|ri|i)+',  '(((p+)r)+i)+')

