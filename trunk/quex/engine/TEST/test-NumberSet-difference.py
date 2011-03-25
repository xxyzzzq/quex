#! /usr/bin/env python
import test_NumberSet_base
import sys
import os
from copy import deepcopy
sys.path.append(os.environ["QUEX_PATH"])
from quex.core_engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Difference"
    sys.exit(0)

def the_difference(Comment, A, B):
    print "#\n#" + Comment
    print "#  A          = " + repr(A)
    print "#  B          = " + repr(B)
    print "#  difference(A,B) = " + repr(A.difference(B))
    print "#  difference(B,A) = " + repr(B.difference(A))

test_NumberSet_base.do("DIFFERENCE", the_difference)    

# some more tests:
X = deepcopy(test_NumberSet_base.A6)
the_difference("Special Case 10", X, NumberSet([Interval(0, 1), Interval(1000, 1001)]))
