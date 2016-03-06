#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine      as regex
import quex.engine.state_machine.algorithm.beautifier as beautifier
import quex.engine.state_machine.algebra.complement as complement
import quex.engine.state_machine.algebra.intersection  as intersection
import quex.engine.state_machine.algebra.union   as union
from   quex.engine.state_machine.check.special   import is_all, is_none, get_all, get_none
import quex.engine.state_machine.check.identity  as identity

if "--hwut-info" in sys.argv:
    print "Complementary State Machines"
    print "CHOICES: Sequence, Branches, Loops, BranchesLoops, Misc;"
    sys.exit(0)

def test(A_str):
    print "_____________________________________________________________________"
    if isinstance(A_str, (str, unicode)):
        print ("A = " + A_str).replace("\n", "\\n").replace("\t", "\\t")
        sm = regex.do(A_str, {}).sm
    else:
        sm = A_str
        print "A = ", sm

    result_1st    = complement.do(sm)
    print "complement(A):", result_1st
    result_2nd    = complement.do(result_1st)
    print
    print "union(A, complement(A)):            All  =", is_all(union.do([sm, result_1st]))
    print "intersection(A, complement(A)):     None =", is_none(intersection.do([sm, result_1st]))
    print "identity(A, complement(complement(A)):", identity.do(sm, result_2nd)

if "Sequence" in sys.argv:
    test('[0-9]')
    test('[0-9][0-9]')
    test('[0-9][0-9][0-9]')
    test('a(b?)')
    test('ab(c?)')

elif "Branches" in sys.argv:
    test('12|AB')
    test('x(12|AB)')
    test('(12|AB)x')
    test('x(12|AB)x')
    test('x(1?2|A?B)x')
    test('x(1?2?|A?B?)x')

elif "Loops" in sys.argv:
    test('A+')
    test('A(B*)')
    test('A((BC)*)')
    test('((A+)B+)C+')
    test('(ABC|BC|C)+')

elif "BranchesLoops" in sys.argv:
    test('(AB|XY)+')
    test('(AB|XY)((DE|FG)*)')
    test('(((AB|XY)+)(DE|FG)+)(HI|JK)+')
    test('((AB|XY)(DE|FG)(HI|JK)|(DE|FG)(HI|JK)|(HI|JK))+')

elif "Misc" in sys.argv:
    test('((((((((p+)r)+i)+)n)+t)+e)+r)+')
    test('(printer|rinter|inter|nter|ter|er|r)+')
    test('(p?r?i?n?t?e?r|rinter|inter|nter|ter|er|r)+')
    test('(((((((((p+)r)+i)+)p)+r)+i)+n)+|(priprin|riprin|iprin|prin|rin|in|n)+)x?')

elif "Special" in sys.argv:
    test(get_none())
    test(get_all())
    sm = get_all()
    sm.get_init_state().set_acceptance(True)
    sm = beautifier.do(sm)
    test(sm)

