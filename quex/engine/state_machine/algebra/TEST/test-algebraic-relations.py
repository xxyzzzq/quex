#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine           as regex
import quex.engine.state_machine.algorithm.beautifier as beautifier
import quex.engine.state_machine.algebra.inverse      as inverse
import quex.engine.state_machine.algebra.reverse      as reverse
import quex.engine.state_machine.algebra.intersection as intersection
import quex.engine.state_machine.algebra.difference   as difference
import quex.engine.state_machine.algebra.union        as union
from   quex.engine.state_machine.check.special        import is_all, is_none
import quex.engine.state_machine.check.identity       as     identity
import quex.engine.state_machine.check.superset       as     superset
from   quex.engine.state_machine.check.special        import get_all, get_none

if "--hwut-info" in sys.argv:
    print "Algebra on Inverse, Reverse, Union, Intersection, Difference"
    sys.exit()

def inv(A):     return inverse.do(A)
def rev(A):     return reverse.do(A)
def uni(*A):    return union.do(list(A))
def itsct(*A):  return intersection.do(list(A))
def diff(A, B): return difference.do(A, B)

protocol = []
X        = None
All_sm   = get_all()
None_sm  = get_none()

def equal(X_str, Y_str):
    global report
    exec("sm0 = " + X_str.replace("All", "All_sm").replace("None", "None_sm"))
    exec("sm1 = " + Y_str.replace("All", "All_sm").replace("None", "None_sm"))
    sm0 = beautifier.do(sm0)
    sm1 = beautifier.do(sm1)
    result = identity.do(sm0, sm1)
    if result is False:
        print "X:", X
        print "X_str", X_str
        print "Y_str", Y_str
        print sm0
        print sm1
        sys.exit()
    protocol.append((X_str, "==", Y_str, result))

def unary(ExprStr):
    global X
    X = regex.do(ExprStr, {}).sm

    equal("inv(inv(X))",           "X")
    equal("rev(rev(X))",           "X")
    #equal("rev(inv(rev(inv(X))))", "X")
    #equal("inv(rev(inv(rev(X))))", "X")

    equal("uni(X, inv(X))", "All")
    equal("uni(inv(X), X)", "All")
    equal("uni(X, None)",   "X")
    equal("uni(None, X)",   "X")
    equal("uni(X, All)",    "All")
    equal("uni(All, X)",    "All")

    equal("itsct(X, inv(X))", "None")
    equal("itsct(inv(X), X)", "None")
    equal("itsct(X, None)",   "None")
    equal("itsct(None, X)",   "None")
    equal("itsct(X, All)",    "X")
    equal("itsct(All, X)",    "X")

    equal("diff(X, inv(X))", "X")
    equal("diff(inv(X), X)", "inv(X) ")
    equal("diff(X, None)",   "X")
    equal("diff(None, X)",   "None")
    equal("diff(X, All)",    "None")
    equal("diff(All, X)",    "inv(X) ")

    report(ExprStr)
    return

def binary(X, Y):

    report("uni(X, Y)",                            "uni(Y, X)")
    report("reverse(uni(reverse(X), reverse(Y)))", "uni(X, Y)")

    report("itsct(X, Y)",                            "itsct(Y, X)")
    report("reverse(itsct(reverse(X), reverse(Y)))", "itsct(X, Y)")

    report("inv(itsct(X, Y))", "uni(inv(X), inv(Y))")
    report("inv(uni(X, Y))", "itsct(inv(X), inv(Y))")

    report("diff(X, Y)",           "itsct(X, inv(Y))")
    report("itsct(diff(X, Y), X)", "None")
    report("uni(diff(X, Y), Y)",   "uni(X, Y)")

def report(ExprStr):
    global protocol
    print "%s %s" % (ExprStr, "_" * (79 - len(ExprStr)))
    print
    L0 = max(len(x[0]) for x in protocol)
    L2 = max(len(x[2]) for x in protocol)
    for x in protocol:
        txt = "  %s%s %s %s%s %s" % (x[0], " " * (L0 - len(x[0])), 
                                     x[1], 
                                     x[2], " " * (L0 - len(x[2])), 
                                     { True: "[OK]", False: "[FAIL]", }[x[3]])
        if x[3] == True:
            print "##%s" % txt
        else:
            print "  %s" % txt
    print

print
unary("A")
unary("AB")
unary("ABC")
unary("(((A+)B+)C+)|ABC|AB")
unary("(((A+)B+)C+)")
