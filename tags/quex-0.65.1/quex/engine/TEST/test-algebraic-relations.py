#! /usr/bin/env python
import sys
import os
from   copy import copy
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.interval_handling import NumberSet, Interval

if "--hwut-info" in sys.argv:
    print "NumberSet: Algebraic Relations;"
    print "CHOICES: unary, binary;"
    sys.exit()

def inv(A):     
    result = A.inverse()
    result.assert_consistency()
    return result

def uni(*A):    
    result   = A[0].clone()
    result_x = result.clone()
    for a in A[1:]: 
        result.unite_with(a)
        result_x = result_x.union(a)

    assert result.is_equal(result_x)
    result.assert_consistency()
    return result

def itsct(*A):  
    result   = A[0].clone()
    result_x = result.clone()
    for a in A[1:]: 
        result.intersect_with(a)
        result_x = result_x.intersection(a)

    assert result.is_equal(result_x)
    result.assert_consistency()
    return result

def diff(A, B): 
    result   = A.difference(B)
    result_x = A.clone()
    result_x.subtract(B)

    assert result.is_equal(result_x)
    result.assert_consistency()
    return result

def symdiff(A, B): 
    result   = A.symmetric_difference(B)
    result.assert_consistency()
    return result

protocol = []
X        = None
S_All    = NumberSet(Interval(-sys.maxint, sys.maxint))
S_None   = NumberSet()

correct_n = 0
def equal(X_str, Y_str):
    global correct_n
    exec("x = " + X_str.replace("All", "S_All").replace("None", "S_None"))
    exec("y = " + Y_str.replace("All", "S_All").replace("None", "S_None"))
    result = x.is_equal(y)
    assert result == True
    assert result != x.is_equal(y.inverse())
    assert result != y.is_equal(x.inverse())
    correct_n += 1

def unary(TheList):
    global correct_n
    global X
    correct_n = 0
    X = NumberSet([Interval(p,q) for p,q in TheList])
    print "# %s ---------------------" % X
    equal("inv(inv(X))",           "X")

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

    equal("symdiff(X, inv(X))", "All")
    equal("symdiff(inv(X), X)", "All")
    equal("symdiff(X, None)",   "X")
    equal("symdiff(None, X)",   "X")
    equal("symdiff(X, All)",    "inv(X)")
    equal("symdiff(All, X)",    "inv(X) ")

    print "No abort --> %i x korrekt" % correct_n
    return

def binary(X_ns, Y_ns):
    global correct_n 
    global X
    global Y
    X = X_ns
    Y = Y_ns
    equal("uni(X, Y)",        "uni(Y, X)")
    equal("itsct(X, Y)",      "itsct(Y, X)")

    equal("inv(itsct(X, Y))", "uni(inv(X), inv(Y))")
    equal("inv(uni(X, Y))",   "itsct(inv(X), inv(Y))")

    equal("diff(X, Y)",                        "itsct(X, inv(Y))")
    equal("itsct(diff(X, Y), Y)",              "None")
    equal("uni(diff(X, Y), Y)",                "uni(X, Y)")
    equal("itsct(symdiff(X, Y), itsct(X, Y))", "None")
    equal("itsct(symdiff(Y, X), itsct(Y, X))", "None")

    return

print
if "unary" in sys.argv:
    unary([(0,1)])
    unary([(-1,0)])
    unary([(-1,1)])
    unary([(-sys.maxint, sys.maxint)])
    unary([])
    unary([(0,1), (2,3)])
    unary([(0,1), (1,2)])

    unary([(0,               100)])
    unary([(0,               sys.maxint)])
    unary([(-sys.maxint,     0)])
    unary([(-sys.maxint,     sys.maxint)])

    unary([(0,         100), (500, 600)])
    unary([(0,         100), (500, sys.maxint)])
    unary([(-sys.maxint, 0), (500, 600)])
    unary([(-sys.maxint, 0), (500, sys.maxint)])

    unary([(0,         100), (100, 200), (500, 600)])
    unary([(0,         100), (100, 200), (500, sys.maxint)])
    unary([(-sys.maxint, 0), (100, 200), (500, 600)])
    unary([(-sys.maxint, 0), (100, 200), (500, sys.maxint)])

elif "binary" in sys.argv:
    correct_n = 0
    def interval_n_iterable():
        for i in xrange(4):
            for j in xrange(i, 4):
                yield (i, j)

    def get_border_list(IntervalN):
        border_n   = IntervalN * 2  # 1 begin +  1 end
        field_n    = IntervalN * 3
        result     = [0] * (border_n + 2)
        result[0]  = -1
        result[-1] = field_n

        for i in xrange(1, border_n):
            result[i+1] = i
        return result

    def increment(cursor):
        i = 1
        while i < len(cursor) - 1:
            if cursor[i] == cursor[i+1] - 1:
                cursor[i] = cursor[i-1] + 1
                i += 1
            else:
                cursor[i] += 1
                return True
        return False

    def get_number_set(Cursor):
        if len(Cursor) == 2:
            return S_None
        cursor = copy(Cursor)
        cursor.pop(0) # element 0 and '-1' are just helping values, no interval borders.
        result = []
        while len(cursor) != 1:
            begin = cursor.pop(0)
            end   = cursor.pop(0)
            result.append(Interval(begin, end))
        return NumberSet(result)

    for interval_n_0, interval_n_1 in [(1,1), (1, 2), (1, 3), (2,2), (2, 3)]:
        cursor_0_orig = get_border_list(interval_n_0)
        cursor_1      = get_border_list(interval_n_1)
        cursor_0      = copy(cursor_0_orig)

        while 1 + 1 == 2:
            binary(get_number_set(cursor_0), get_number_set(cursor_1))

            if increment(cursor_0) == False: 
                cursor_0 = copy(cursor_0_orig)
                if increment(cursor_1) == False:
                    break

    print "No abort --> %i x korrekt" % correct_n

