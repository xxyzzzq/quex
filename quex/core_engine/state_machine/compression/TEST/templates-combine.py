#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.templates as templates 
from   quex.core_engine.state_machine.compression.TEST.templates_aux import *

if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Combine Trigger Maps"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TMa, TMb, InvolvedStateListA = [10L], InvolvedStateListB = [20L]):
    print
    print "(Straight)---------------------------------------"
    print
    print_tm(TMa)
    print_tm(TMb)
    print
    result = templates.get_combined_trigger_map(TMa, InvolvedStateListA, 
                                                TMb, InvolvedStateListB)
    print_tm(result)
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(TMb)
    print_tm(TMa)
    print
    print_tm(templates.get_combined_trigger_map(TMb, InvolvedStateListB, 
                                                TMa, InvolvedStateListA))
    print

tm0 = [ 
        (Interval(-sys.maxint, 10), 1L),
        (Interval(10, sys.maxint),  2L),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 30), 1L),
            (Interval(30, sys.maxint),  2L),
          ]
    test(tm0, tm1)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), 2L),
            (Interval(10, sys.maxint),  1L),
          ]
    test(tm0, tm1)

elif "2b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), 1L),
            (Interval(10, sys.maxint),  2L),
          ]
    test(tm0, tm1)

elif "3" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 5),  1L),
            (Interval(5, 15),           2L),
            (Interval(15, 20),          3L),
            (Interval(20, 25),          4L),
            (Interval(25, 30),          5L),
            (Interval(30, 35),          6L),
            (Interval(35, sys.maxint),  7L),
          ]
    test(tm0, tm1)

elif "4" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, sys.maxint), 2L),
          ]
    tm1 = [ 
            (Interval(-sys.maxint, 20), 2L),
            (Interval(20, sys.maxint),  1L),
          ]
    test(tm0, tm1)

elif "recursive" in sys.argv:
    print "Involved states in First = 1L"
    print "Involved states in Second = 2L"
    print "=> when First triggers to 1L and Second to 2L, then both"
    print "   are recursive and no distinction needs to be made."
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 2L),
          ]
    test(tm0, tm1, [1L], [2L])
    print "(1L, 2L) has not to appear, but '-2' to indicate recursion."


