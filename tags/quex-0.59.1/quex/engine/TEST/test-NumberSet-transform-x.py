#! /usr/bin/env python
from   copy import deepcopy
from   random import random
import test_NumberSet_base

import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
from quex.engine.interval_handling import Interval, NumberSet

if "--hwut-info" in sys.argv:
    print "NumberSet: Transform Large NumberSets / Transformations;"
    print "CHOICES:   10, 100, 250, 500, 1000, 2000, 3000;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Require at least one argument."
    sys.exit(-1)

maximum = float(sys.argv[1])

def verify(A, TrafoInfo):
    result = NumberSet()

    for interval in A.get_intervals():
        for x in range(interval.begin, interval.end):
            for source_begin, source_end, target_begin in TrafoInfo:
                if x >= source_begin and x < source_end:
                    offset = x - source_begin
                    y      = target_begin + offset
                    result.quick_append_interval(Interval(y))

    result.clean()
    return result

def create_random_interval_list(ContinuousF):
    """Note: 'random()' always delivers the same value when its called the n-th time."""
    global maximum
    interval_n    = int(maximum)
    interval_list = [] 
    cursor        = 0
    for i in range(interval_n):
        end = cursor + 1 + int(random() * 3)

        # The 'third' element is required for transformation infos. A transformation
        # info is continuous, a number set is not.
        if ContinuousF: interval_list.append([cursor, end, i * 100])
        else:           interval_list.append([cursor, end])

        if ContinuousF: cursor = end
        else:           cursor = end + int(random() * 3)

    return interval_list

def create_random_number_set():
    result = NumberSet()
    for begin, end in create_random_interval_list(False):
        result.quick_append_interval(Interval(begin, end))
    return result

def create_random_transformation_info():
    return create_random_interval_list(True)


def test(Comment, A, TrafoInfo):
    global maximum
    print "#\n# " + repr(maximum) + " " + "_" * (80 - len(Comment))
    x = deepcopy(A)
    ## print "#  A       = " + repr(x)
    ## print "#  Trafo   = " + repr(TrafoInfo)
    x.transform(TrafoInfo)
    ## print "#  Result  = " + repr(x)
    result = verify(A, TrafoInfo)
    ## print "#  Verify  = " + repr(result)
    print "#  CheckF  = " + repr(x.is_equal(result))
    print "#"

test("All in 1", create_random_number_set(), create_random_transformation_info())
