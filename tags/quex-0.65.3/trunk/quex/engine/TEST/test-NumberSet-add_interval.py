#! /usr/bin/env python
from   copy import deepcopy
import test_NumberSet_base

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.misc.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Add Interval"
    sys.exit(0)

def test(Comment, A, B, ViceVersaF=True):
    if B.__class__ == Interval: B = NumberSet(B)

    def __do_this(A, B):
        interval_list = B.get_intervals()
        for interval in interval_list:
            print "#"
            print "#  A                 = " + repr(A)
            print "#  B                 = " + repr(interval)
            X = deepcopy(A)
            safe = Interval(interval.begin, interval.end)
            X.add_interval(safe)
            X.assert_consistency()
            safe.begin = 7777
            safe.end   = 0000
            print "#  A.add_interval(B) = " + repr(X) 

    print "#\n# " + Comment + "_" * (80 - len(Comment))
    __do_this(A, B)
    if ViceVersaF: __do_this(B, A)

test_NumberSet_base.do("ADD_INTERVAL", test)    

# some more tests:
X = deepcopy(test_NumberSet_base.A6)
test("Special Case 1", X,  Interval(10, 130),   ViceVersaF=False)
test("Special Case 2", X,  Interval(10, 280),   ViceVersaF=False)
test("Special Case 3", X,  Interval(10, 129),   ViceVersaF=False)
test("Special Case 4", X,  Interval(10, 279),   ViceVersaF=False)
test("Special Case 5", X,  Interval(11, 130),   ViceVersaF=False)
test("Special Case 6", X,  Interval(0, 1000),   ViceVersaF=False)
test("Special Case 7", X,  Interval(15, 210),   ViceVersaF=False)
test("Special Case 8", X,  Interval(210, 1000), ViceVersaF=False)
test("Special Case 9", X,  Interval(150, 251),  ViceVersaF=False)
test("Special Case 10", X, Interval(0),         ViceVersaF=False)
test("Special Case 11", X, Interval(9),         ViceVersaF=False)
test("Special Case 12", X, Interval(10),        ViceVersaF=False)
test("Special Case 13", X, Interval(11),        ViceVersaF=False)
test("Special Case 14", X, Interval(278),       ViceVersaF=False)
test("Special Case 15", X, Interval(279),       ViceVersaF=False)
test("Special Case 16", X, Interval(280),       ViceVersaF=False)
test("Special Case 17", X, Interval(0,2),       ViceVersaF=False)
test("Special Case 18", X, Interval(9,11),      ViceVersaF=False)
test("Special Case 19", X, Interval(10,12),     ViceVersaF=False)
test("Special Case 20", X, Interval(11,13),     ViceVersaF=False)
test("Special Case 21", X, Interval(278,280),   ViceVersaF=False)
test("Special Case 22", X, Interval(279,281),   ViceVersaF=False)
test("Special Case 23", X, Interval(280,282),   ViceVersaF=False)
