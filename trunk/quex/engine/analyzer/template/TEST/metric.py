#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.template.state              import combine_maps
from   quex.engine.analyzer.template.TEST.templates_aux import *
from   quex.engine.interval_handling import *

from   quex.blackboard  import E_StateIndices



if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Target Idx Combination Metric"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TriggerMapA, StateN_A, TriggerMapB, StateN_B, UniformEntriesF=True):

    analyzer, state_a, state_b = configure_States(TriggerMapA, StateN_A, TriggerMapB, StateN_B)

    print
    print "(Straight)---------------------------------------"
    test_combination(state_a, state_b, analyzer)
    print "(Vice Versa)-------------------------------------"
    test_combination(state_b, state_a, analyzer)

tm0 = [ 
        (Interval(-sys.maxint, 10), [10L, 11L]),
        (Interval(10, sys.maxint),  [20L, 21L]),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 30), [10L, 11L]),
            (Interval(30, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, 2, tm1, 2)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [20L, 21L]),
            (Interval(10, sys.maxint),  [10L, 11L])
          ]
    test(tm0, 2, tm1, 2)

elif "2b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [10L, 11L]),
            (Interval(10, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, 2, tm1, 2)

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
    test(tm0, 2, tm1, 2)

elif "4" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, sys.maxint), [20L, 21L]),
          ]
    tm1 = [ 
            (Interval(-sys.maxint, 20), [20L, 21L]), 
            (Interval(20, sys.maxint),  [10L, 11L]), 
          ]
    test(tm0, 2, tm1, 2)

elif "recursive" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), (2L, 3L)),
          ]
    test(tm0, 2, tm1, 2)

