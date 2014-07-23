#! /usr/bin/env python
from   copy import deepcopy

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Transform"
    print "CHOICES:   1, 2, 3;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Require at least one argument."
    sys.exit(-1)

def verify(A, TrafoInfo):
    result = NumberSet()
    for interval in A.get_intervals():
        for x in range(interval.begin, interval.end):
            for source_begin, source_end, target_begin in TrafoInfo:
                if x >= source_begin and x < source_end:
                    offset = x - source_begin
                    y      = target_begin + offset
                    result.add_interval(Interval(y))
    result.assert_consistency()
    return result

def test(Comment, A, TrafoInfo):
    print "#\n# " + Comment + " " + "_" * (80 - len(Comment))
    print "#"
    x = deepcopy(A)
    print "#  A       = " + repr(x)
    print "#  Trafo   = " + repr(TrafoInfo)
    x.transform(TrafoInfo)
    x.assert_consistency()
    print "#  Result  = " + repr(x)
    result = verify(A, TrafoInfo)
    print "#  Verify  = " + repr(result)
    print "#  CheckF  = " + repr(x.is_equal(result))
    x = deepcopy(A)
    #  Adding unrelated transformations:
    x.transform([[0, 1, 5]] + TrafoInfo + [[30, 40, 200]])
    print "#  ResultX = " + repr(x)

choice_i = int(sys.argv[1])
# some more tests:
X = { 1: NumberSet([Interval(10,20)]),
      2: NumberSet([Interval(10,15), Interval(16,20)]),
      3: NumberSet([Interval(10,13), Interval(14,17), Interval(18,20)]),
      }[choice_i]
test("All in 1",                         X, [[0, 20, 100]])
test("%i in interval 0"      % choice_i, X, [[0, 20, 100], [25, 30, 200]])
test("%i in interval 1"      % choice_i, X, [[0, 10, 100], [10, 20, 200]])
test("%i in intervals 0,1"   % choice_i, X, [[0, 15, 100], [15, 20, 200]])
if choice_i == 2:
    test("%i in intervals 0,1 - x"  % choice_i, X, [[0, 14, 100], [14, 20, 200]])
    test("%i in intervals 0,1 - xx" % choice_i, X, [[0, 17, 100], [17, 20, 200]])
test("%i in intervals 0,1,2" % choice_i, X, [[0, 13, 100], [13, 16, 200], [16, 20, 300]])
if choice_i == 3:
    test("%i in intervals 0,1,2" % choice_i, X, [[0, 11, 100], [11, 12, 200], [12, 20, 300]])
