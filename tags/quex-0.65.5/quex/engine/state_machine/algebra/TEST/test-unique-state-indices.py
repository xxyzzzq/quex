#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine                   as regex
import quex.engine.state_machine.algorithm.beautifier         as beautifier
import quex.engine.state_machine.algebra.complement           as complement
import quex.engine.state_machine.algebra.reverse              as reverse
import quex.engine.state_machine.algebra.intersection         as intersection
import quex.engine.state_machine.algebra.difference           as difference
import quex.engine.state_machine.algebra.symmetric_difference as symmetric_difference
import quex.engine.state_machine.algebra.complement_begin     as complement_begin
import quex.engine.state_machine.algebra.complement_end       as complement_end  
import quex.engine.state_machine.algebra.complement_end       as complement_in  
import quex.engine.state_machine.algebra.union                as union
from   quex.engine.state_machine.check.special                import is_all, is_none
import quex.engine.state_machine.check.identity               as     identity
import quex.engine.state_machine.check.superset               as     superset
from   quex.engine.state_machine.check.special                import get_all, get_none

from   itertools import islice

if "--hwut-info" in sys.argv:
    print "Unique State Indices;"
    sys.exit()

def test(Name, function, ExprStrX, ExprStrY, ExprStrZ):
    global X
    global Y
    X = regex.do(ExprStrX, {}).sm
    Y = regex.do(ExprStrY, {}).sm
    Z = regex.do(ExprStrZ, {}).sm

    if Name in ["NotIn", "NotBegin", "NotEnd", "Difference"]:
        r0 = function(X, Y)
        r1 = function(X, Z)
    else:
        r0 = function([X, Y])
        r1 = function([X, Z])

    state_indices_0 = set(r0.states.iterkeys())
    state_indices_1 = set(r1.states.iterkeys())

    print "%s _________________________________________" % Name
    if not state_indices_0.isdisjoint(state_indices_1):
        print "Error: Two results contain common state indices."
        print "Error:", state_indices_0.intersection(state_indices_1)

    else:
        print "Oll Korrect"

test("NotBegin",            complement_begin.do,     "(otto|fritz)_muller", "otto",          "fritz")
test("NotEnd",              complement_end.do,       "otto_(meyer|muller)", "meyer",         "mueller")
test("NotIn",               complement_in.do,        "fore(v|st)er",        "v",             "st")
test("Union",               union.do,                "otto_muller",         "fritz_mueller", "heinz_mueller")
test("Intersection",        intersection.do,         "(otto|fritz)_muller", "otto_mueller",  "fritz_mueller")
test("Difference",          difference.do,           "(otto|fritz)_muller", "otto_mueller",  "fritz_mueller")
test("SymmetricDifference", symmetric_difference.do, "(otto|fritz)_muller", "otto_mueller",  "fritz_mueller")


