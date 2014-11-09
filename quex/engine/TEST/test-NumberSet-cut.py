#! /usr/bin/env python
from   copy import deepcopy
import test_NumberSet_base

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.misc.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Cut;"
    print "CHOICES:   empty, 1, 1b, 2, 2b, 3, 3b;"
    sys.exit(0)


def test(Border, List):
    x = NumberSet([Interval(a, b) for a, b in List])
    y = deepcopy(x)
    z = deepcopy(x)
    print "Border:              %s" % Border
    print "NumberSet:           %s" % x
    x.cut_lesser(Border)
    x.assert_consistency()
    y.cut_greater_or_equal(Border)
    x.assert_consistency()
    print "cut_lesser           --> %s" % x
    print "cut_greater_or_equal --> %s" % y
    print "______________________________________"

    assert x.union(y).is_equal(z)

def border_list(Intervals):
    collection = set()
    for X in Intervals:
        collection.update([X[0] - 1, X[0], X[0] + 1, X[1] - 1, X[1], X[1] + 1])
    return sorted(list(collection))

def run(*Intervals):
    for border in border_list(Intervals):
        test(border, Intervals)

if "empty" in sys.argv:
    for border in [0, 65536]:
        test(border, [])

if "1" in sys.argv:
    run((10, 20))

if "2" in sys.argv:
    run((10, 20), (30, 40))

if "3" in sys.argv:
    run((10, 20), (30, 40), (50, 60))

if "1b" in sys.argv:
    run((10, 11))

if "2b" in sys.argv:
    run((10, 11), (20, 21))

if "3b" in sys.argv:
    run((10, 11), (20, 21), (30, 31))

