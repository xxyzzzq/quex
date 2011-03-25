#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.templates as templates 
from   quex.core_engine.state_machine.compression.TEST.templates_aux import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Combine Combined Trigger Maps"
    print "CHOICES: 1, 2, recursive, recursive-2, recursive-3;"
    sys.exit(0)

def test(TriggerMapA, StateN_A, TriggerMapB, StateN_B, DoNotMakeCombinationF=True):
    StateListA = range(10, 10 + StateN_A)
    if StateN_A > 1: CombinationA = get_combination(TriggerMapA, StateListA)
    else:            CombinationA = TriggerMapA
    StateListB = range(20, 20 + StateN_B)
    if StateN_B > 1: CombinationB = get_combination(TriggerMapB, StateListB)
    else:            CombinationB = TriggerMapB

    print
    print "(Straight)---------------------------------------"
    print
    print_tm(CombinationA)
    print_tm(CombinationB)
    print
    result = templates.get_combined_trigger_map(CombinationA, StateListA, CombinationB, StateListB)
    print_tm(result)
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(CombinationB)
    print_tm(CombinationA)
    print
    print_tm(templates.get_combined_trigger_map(CombinationB, StateListB, CombinationA, StateListA))
    print

tm0 = [ 
        (Interval(-sys.maxint, 20), [1L, 2L, 3L]),
        (Interval(20, sys.maxint),  1L),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [1L, 2L, 3L]),
            (Interval(10, 20),          1L),
            (Interval(20, 30),          [1L, 2L, 3L]),
            (Interval(30, sys.maxint),  1L),
          ]
    test(tm0, 3, tm1, 3)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [1L, 2L, 3L]),
            (Interval(10, 20),          2L),
            (Interval(20, 30),          [3L, 4L, 5L]),
            (Interval(30, sys.maxint),  2L),
          ]
    test(tm0, 3, tm1, 3)

elif "recursive" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), -2L),
          ]
    test(tm0, 3, tm1, 3)

elif "recursive-2" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), [1L, 2L]),    # This is not recursive
            (Interval(20, sys.maxint),  10L),         # This is not recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-3" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), [1L, 2L]),    # This is not recursive
            (Interval(20, sys.maxint),  -2L),         # This is recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

