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

from   itertools import islice

if "--hwut-info" in sys.argv:
    print "Algebraic Relations;"
    print "CHOICES:  unary, binary;"
    sys.exit()

def inv(A):     return inverse.do(A)
def rev(A):     return reverse.do(A)
def uni(*A):    return union.do(list(A))
def itsct(*A):  return intersection.do(list(A))
def diff(A, B): return difference.do(A, B)

def exec_print(ExprStr):
    exec("sme = %s" % ExprStr)
    print "%s: -->" % ExprStr
    print beautifier.do(sme)

protocol = []
X        = None
Y        = None
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
        print "Y:", Y
        exec_print("uni(X, Y)")
        exec_print("inv(uni(X, Y))")
        print "%s: -->\n%s" % (X_str, sm0)
        print "%s: -->\n%s" % (Y_str, sm1)
        sys.exit()
    protocol.append((X_str, "==", Y_str, result))

def unary(ExprStr):
    global X
    global protocol
    del protocol[:]
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

def binary(ExprStrX, ExprStrY):
    global X
    global Y
    X = regex.do(ExprStrX, {}).sm
    Y = regex.do(ExprStrY, {}).sm

    equal("uni(X, Y)",                  "uni(Y, X)")
    equal("itsct(X, Y)",                "itsct(Y, X)")

    equal("rev(uni(rev(X), rev(Y)))",   "uni(X, Y)")
    equal("rev(itsct(rev(X), rev(Y)))", "itsct(X, Y)")

    equal("inv(itsct(X, Y))", "uni(inv(X), inv(Y))")
    equal("inv(uni(X, Y))",   "itsct(inv(X), inv(Y))")

    equal("diff(X, Y)",           "itsct(X, inv(Y))")
    equal("itsct(diff(X, Y), Y)", "None")
    equal("uni(diff(X, Y), Y)",   "uni(X, Y)")

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

pattern_list = [
    "A",
    "AB",
    "ABC",
    "A((BC)|(DE))F",
    "A((BC)|(DE))*F",
    "A((BC)|(DE?))*F",
    "(((A+)B+)C+)|ABC|AB",
    "(((A+)B+)C+)",
    "0(((A*)(B+C)*)((C+D)*)E+)*",
    #"\Any*",
    #"\None",
]

if "unary" in sys.argv:
    for pattern_str in pattern_list:
        unary(pattern_str)

elif "binary" in sys.argv:
    for i, str_0 in enumerate(pattern_list):
        for str_1 in islice(pattern_list, i):
            binary(str_0, str_1)

    # If no assert triggers, then everything is OK
    print "Oll Korrekt"


