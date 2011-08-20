#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.interval_handling import *
import quex.engine.state_machine.compression.templates as templates 
from   quex.engine.state_machine.compression.TEST.templates_aux import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Single Target Idx Metric"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TMa, TMb, InvolvedStateListA=[10L], InvolvedStateListB=[20L]):
    print
    print "(Straight)---------------------------------------"
    print
    print_tm(TMa)
    print_tm(TMb)
    print
    print_metric(templates.get_metric(TMa, InvolvedStateListA, TMb, InvolvedStateListB))
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(TMb)
    print_tm(TMa)
    print
    print_metric(templates.get_metric(TMb, InvolvedStateListB, TMa, InvolvedStateListA))
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
            (Interval(-sys.maxint, 5),  2L),
            (Interval(5, 15),           3L),
            (Interval(20, 25),          4L),
            (Interval(25, 30),          5L),
            (Interval(35, sys.maxint),  1L),
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
    print "A target combination (1L, 2L) and vice versa has not to appear,"
    print "because this would mean recursion and is thus an equivalence."

