#! /usr/bin/env python
import test_NumberSet_base
import sys
import os
from copy import deepcopy
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Intersection"
    sys.exit(0)

def the_intersection(Comment, A, B):
    if B.__class__ == Interval: B = NumberSet(B)

    print "#\n#" + Comment
    print "#  A          = " + repr(A)
    print "#  B          = " + repr(B)
    print "#  intersection(A,B) = " + repr(A.intersection(B))
    print "#  intersection(B,A) = " + repr(B.intersection(A))

test_NumberSet_base.do("INTERSECTION", the_intersection)    

# some more tests:
X = deepcopy(test_NumberSet_base.A6)
the_intersection("Special Case 1", X, Interval(10, 130))
the_intersection("Special Case 2", X, Interval(10, 280))
the_intersection("Special Case 3", X, Interval(10, 129))
the_intersection("Special Case 4", X, Interval(10, 279))
the_intersection("Special Case 5", X, Interval(11, 130))
the_intersection("Special Case 6", X, Interval(0, 1000))
the_intersection("Special Case 7", X, Interval(15, 210))
the_intersection("Special Case 8", X, Interval(210, 1000))
the_intersection("Special Case 9", X, Interval(150, 251))
the_intersection("Special Case 10", X, NumberSet([Interval(0, 1), Interval(1000, 1001)]))
