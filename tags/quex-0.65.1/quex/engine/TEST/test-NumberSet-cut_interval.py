#! /usr/bin/env python
from   copy import deepcopy
import test_NumberSet_base

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Cut Interval"
    sys.exit(0)

def the_difference(Comment, A, B, ViceVersaF=True):
    if B.__class__ == Interval: B = NumberSet(B)

    def __do_this(A, B):
        interval_list = B.get_intervals()
        for interval in interval_list:
            print "#"
            print "#  A                 = " + repr(A)
            print "#  B                 = " + repr(interval)
            X = deepcopy(A)
            safe = Interval(interval.begin, interval.end)
            X.cut_interval(safe)
            X.assert_consistency()
            safe.begin = 7777
            safe.end   = 0000
            print "#  A.cut_interval(B) = " + repr(X) 

    print "#\n# " + Comment + "_" * (80 - len(Comment))
    __do_this(A, B)
    if ViceVersaF: __do_this(B, A)

test_NumberSet_base.do("CUT_INTERVAL", the_difference)    

# some more tests:
X = deepcopy(test_NumberSet_base.A6)
the_difference("Special Case 1", X, Interval(10, 130), ViceVersaF=False)
the_difference("Special Case 2", X, Interval(10, 280), ViceVersaF=False)
the_difference("Special Case 3", X, Interval(10, 129), ViceVersaF=False)
the_difference("Special Case 4", X, Interval(10, 279), ViceVersaF=False)
the_difference("Special Case 5", X, Interval(11, 130), ViceVersaF=False)
the_difference("Special Case 6", X, Interval(0, 1000), ViceVersaF=False)
the_difference("Special Case 7", X, Interval(15, 210),   ViceVersaF=False)
the_difference("Special Case 8", X, Interval(210, 1000), ViceVersaF=False)
the_difference("Special Case 9", X, Interval(150, 251),  ViceVersaF=False)
