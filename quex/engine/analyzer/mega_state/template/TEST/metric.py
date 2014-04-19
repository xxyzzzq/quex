#! /usr/bin/env python
#
# PURPOSE: 
#
# In a template state, two transition maps are combined into one. The new 
# combination has a certain 'cost'. A gain is the difference between the 
# cost of two separate transition maps versus the cost of a combined transition
# map in a template state.
#
# The tests in this file investigate whether:
#
#  -- The transition maps are properly combined, and
#  -- whether the found cost and gain values make sense.
#
# PROCEDURE:
#
# Each test considers two transition maps to be combined. With the two maps
# the following happens:
#
#  (1) Show transition maps and print out the 'cost' of each.
#  (2) Combine both transition maps into one.
#  (3) Display the cost of the real resulting combination.
#  (4) Display of the estimated cost.
#  (5) Display gain, real and estimated.
#
# Real values and estimated values must be the same.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.mega_state.template.state              import combine_maps
from   quex.engine.analyzer.mega_state.template.candidate          import __transition_map_cost, \
                                                                          _transition_map_gain, \
                                                                          _transition_cost_combined
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *
from   quex.engine.interval_handling import *

from   quex.blackboard  import E_StateIndices



if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Target Idx Combination Metric"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def handle_tm(Name, Tm, ImplementedStateIndexList, SchemeN):
    print "%s:" % Name
    print_tm(Tm, ImplementedStateIndexList, OnlyStateIndexF=True)
    cost = __transition_map_cost(len(ImplementedStateIndexList),
                                len(Tm), SchemeN)
    print "cost(%s): %s" % (Name, cost)
    return cost

def determine_scheme_n(TM):
    scheme_set = set()
    for interval, target in TM:
        scheme_set.add(tuple(target.iterable_door_id_scheme()))
    return len(scheme_set)

def test_combine_maps(A, B):
    A_scheme_n = determine_scheme_n(A)
    B_scheme_n = determine_scheme_n(B)
    cost_A = handle_tm("A", A, [1,2,3], A_scheme_n)
    cost_B = handle_tm("B", B, [4,5,6], B_scheme_n)

    result, scheme_n = combine_maps(A, B)
    print
    cost_result_est = _transition_cost_combined(A, B, ImplementedStateN=6)
    cost_result     = handle_tm("result", result, [1,2,3,4,5,6], scheme_n)
    print "cost(result, estimated):", cost_result_est
    assert cost_result == cost_result_est
    print 

    gain = (cost_A + cost_B - cost_result)
    gain_est = _transition_map_gain(ATm=A, AStateN=3, ASchemeN=A_scheme_n,
                                        BTm=B, BStateN=3, BSchemeN=B_scheme_n)
    print "=> gain:           ", gain
    print "=> gain(estimated):", gain_est
    assert gain == gain_est
    print "[OK]"
    print
    return cost_result, gain

def test(TriggerMapA, TriggerMapB):
    tmA = get_TransitionMap_with_TargetByStateKeys(TriggerMapA)
    tmB = get_TransitionMap_with_TargetByStateKeys(TriggerMapB)

    print
    print "(Straight)---------------------------------------"
    cost0, gain0 = test_combine_maps(tmA, tmB)
    print "(Vice Versa)-------------------------------------"
    cost1, gain1 = test_combine_maps(tmB, tmA)

    assert cost0 == cost1
    assert gain0 == gain1

tm0 = [ 
    (Interval(-sys.maxint, 10), [10L, 11L]),
    (Interval(10, sys.maxint),  [20L, 21L]),
]

if "1" in sys.argv:
    tm1 = [ 
        (Interval(-sys.maxint, 30), [10L, 11L]),
        (Interval(30, sys.maxint),  [20L, 21L]),
    ]

elif "2" in sys.argv:
    tm1 = [ 
        (Interval(-sys.maxint, 10), [20L, 21L]),
        (Interval(10, sys.maxint),  [10L, 11L])
    ]

elif "2b" in sys.argv:
    tm1 = [ 
        (Interval(-sys.maxint, 10), [10L, 11L]),
        (Interval(10, sys.maxint),  [20L, 21L]),
    ]

elif "3" in sys.argv:
    tm1 = [ 
        # (Interval(-sys.maxint, 5),  [20L, 21L]),
        # (Interval(5, 15),           [30L, 31L]),
        # (Interval(20, 25),          [40L, 41L]),
        # (Interval(25, 30),          [50L, 51L]),
        # (Interval(35, sys.maxint),  [10L, 20L]),
        (Interval(-sys.maxint, 5),  [20L, 21L]),
        (Interval(5, 20),           [30L, 31L]),
        (Interval(20, 25),          [40L, 41L]),
        (Interval(25, 35),          [50L, 51L]),
        (Interval(35, sys.maxint),  [10L, 20L]),
    ]

elif "4" in sys.argv:
    tm0 = [ 
        (Interval(-sys.maxint, sys.maxint), [20L, 21L]),
    ]
    tm1 = [ 
        (Interval(-sys.maxint, 20), [20L, 21L]), 
        (Interval(20, sys.maxint),  [10L, 11L]), 
    ]

elif "recursive" in sys.argv:
    tm1 = [ 
        (Interval(-sys.maxint, sys.maxint), (2L, 3L)),
    ]
test(tm0, tm1)

