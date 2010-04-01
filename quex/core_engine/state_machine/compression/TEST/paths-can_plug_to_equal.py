#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.paths as paths 

if "--hwut-info" in sys.argv:
    print "Paths: can_plug_to_equal;"
    print "CHOICES: 1_interval, 2_intervals;"
    sys.exit(0)
    
def number_set(IntervalList):
    result = NumberSet(map(lambda x: Interval(x[0], x[1]), IntervalList))
    print result
    return result


def test(List0, List1, TestPlugs):
    Set0 = number_set(List0)
    Set1 = number_set(List1)
    for char in TestPlugs:
        forward  = paths.can_plug_to_equal(Set0, Set1, char)
        backward = paths.can_plug_to_equal(Set1, Set0, char)
        print "%02X, %s, %s;" % (char, repr(forward), repr(backward))
    print 


if "1_interval" in sys.argv:
    test([[0, 1]],
         [[0, 2]],
         [-1, 0, 1, 2, 3])

    test([[0, 1]],
         [[0, 1], [3, 4]],
         [-1, 0, 1, 2, 3, 4])

    test([[0, 1]],
         [[0, 1], [3, 4], [5, 6]],
         [-1, 0, 1, 2, 3, 4])

    test([[0, 1]],
         [[0, 1], [3, 6]],
         [-1, 0, 1, 2, 3, 4])
else:

    test([[0, 1], [3, 4]],
         [[0, 1], [3, 5]],
         [-1, 0, 1, 2, 3, 4, 5])

    test([[0, 1], [3, 4]],
         [[0, 1], [3, 4], [6, 7]],
         [-1, 0, 1, 2, 3, 4, 5, 6, 7])

    test([[3, 4], [6, 7]],
         [[0, 1], [3, 4], [6, 7]],
         [-1, 0, 1, 2, 3, 4, 5, 6, 7])

    test([[0, 2], [3, 4]],
         [[0, 4]],
         [-1, 0, 1, 2, 3, 4])

# test([[0, 10], [21, 30]],
#     [[0, 10], [20, 30]],
#     [-1, 0, 10, 11, 19, 20, 21, 33, 34, 35])


