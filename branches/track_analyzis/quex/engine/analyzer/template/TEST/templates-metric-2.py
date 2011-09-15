#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.interval_handling import *
import quex.engine.state_machine.compression.templates as templates 
from   quex.engine.state_machine.compression.TEST.templates_aux import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Target Idx Combination Metric"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TriggerMapA, TriggerMapB, StateListA=[10L], StateListB=[20L], UniformEntriesF=True):
    StateA = TestTemplateState(TriggerMapA, StateListA)
    StateB = TestTemplateState(TriggerMapB, StateListB)

    print
    print "(Straight)---------------------------------------"
    print
    print_tm(StateA)
    print_tm(StateB)
    print
    result = combine_maps(StateA, StateB, UniformEntriesF)
    print_metric(result)
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(StateB)
    print_tm(StateA)
    print
    result = combine_maps(StateB, StateA, UniformEntriesF)
    print_metric(result)
    print

tm0 = [ 
        (Interval(-sys.maxint, 10), [10L, 11L]),
        (Interval(10, sys.maxint),  [20L, 21L]),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 30), [10L, 11L]),
            (Interval(30, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, tm1)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [20L, 21L]),
            (Interval(10, sys.maxint),  [10L, 11L])
          ]
    test(tm0, tm1)

elif "2b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), [10L, 11L]),
            (Interval(10, sys.maxint),  [20L, 21L]),
          ]
    test(tm0, tm1)

elif "3" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 5),  [20L, 21L]),
            (Interval(5, 15),           [30L, 31L]),
            (Interval(20, 25),          [40L, 41L]),
            (Interval(25, 30),          [50L, 51L]),
            (Interval(35, sys.maxint),  [10L, 20L]),
          ]
    test(tm0, tm1)

elif "4" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, sys.maxint), [20L, 21L]),
          ]
    tm1 = [ 
            (Interval(-sys.maxint, 20), [20L, 21L]), 
            (Interval(20, sys.maxint),  [10L, 11L]), 
          ]
    test(tm0, tm1)

elif "recursive" in sys.argv:
    print "Involved states in First  = [10L, 11L]"
    print "Involved states in Second = [20L, 21L]"
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), -2L),
          ]
    test(tm0, tm1, [10L, 11L], [20L, 21L])

