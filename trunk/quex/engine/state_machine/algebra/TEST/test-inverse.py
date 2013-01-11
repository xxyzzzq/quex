#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine      as regex
import quex.engine.state_machine.algebra.inverse as inverse
import quex.engine.state_machine.algebra.intersection  as intersection
import quex.engine.state_machine.algebra.union   as union
from   quex.engine.state_machine.check.special   import is_all, is_none
import quex.engine.state_machine.check.identity  as identity

if "--hwut-info" in sys.argv:
    print "Inverse State Machines"
    print "CHOICES: Sequence, Branches, Loops, BranchesLoops, Misc;"
    sys.exit(0)

def test(A_str):
    print "_____________________________________________________________________"
    print ("A = " + A_str).replace("\n", "\\n").replace("\t", "\\t")
    a_pattern = regex.do(A_str, {})
    result_1st    = inverse.do(a_pattern.sm)
    print "inverse(A):", result_1st
    result_2nd    = inverse.do(result_1st)
    print
    print "union(A, inverse(A)):            All  =", is_all(union.do([a_pattern.sm, result_1st]))
    print "intersection(A, inverse(A)):     None =", is_none(intersection.do([a_pattern.sm, result_1st]))
    print "identity(A, inverse(inverse(A)):", identity.do(a_pattern.sm, result_2nd)

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

