#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.analyzer.mega_state.template.core               as templates
from   quex.engine.analyzer.mega_state.template.state              import TemplateState, combine_maps
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *

from   quex.engine.interval_handling import *
from   quex.blackboard               import E_StateIndices


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Combine Combined Trigger Maps"
    print "CHOICES: 1, 2, recursive, recursive-2, recursive-3, recursive-b, recursive-2b;"
    sys.exit(0)

def test(TriggerMapA, StateN_A, TriggerMapB, StateN_B, DrawF=True):

    analyzer, state_a, state_b = configure_States(TriggerMapA, StateN_A, TriggerMapB, StateN_B)

    print
    print "(Straight)---------------------------------------"
    combine(analyzer, state_a, state_b, "A", "B", DrawF)
    print "(Vice Versa)-------------------------------------"
    combine(analyzer, state_b, state_a, "A", "B", DrawF)

tm0 = [ 
        (Interval(-sys.maxint, 20), (100L, 200L, 300L)),
        (Interval(20, sys.maxint),  (100L, 100L, 100L)),
      ]

if "1" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), (100L, 200L, 300L)),
            (Interval(10, 20),          (100L, 100L, 100L)),
            (Interval(20, 30),          (100L, 200L, 300L)),
            (Interval(30, sys.maxint),  (100L, 100L, 100L)),
          ]
    test(tm0, 3, tm1, 3, False)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), (100L, 200L, 300L)),
            (Interval(10, 20),          (200L, 100L, 100L)),
            (Interval(20, 30),          (300L, 400L, 500L)),
            (Interval(30, sys.maxint),  (200L, 100L, 100L)),
          ]
    test(tm0, 3, tm1, 3, False)

elif "recursive" in sys.argv:
    tm1 = [ 
            # Recursion in states 3, 4, 5
            (Interval(-sys.maxint, sys.maxint), (3L, 4L, 5L)),  
          ]
    test(tm0, 3, tm1, 3)

elif "recursive-b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), (3L, 4L, 5L)),
          ]
    test(tm0, 3, tm1, 3)

elif "recursive-2" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (10L, 20L)),  # This is not recursive
            (Interval(20, sys.maxint),  (0L, 0L)),    # This is not recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), (2L,)), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-2b" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (1L,  0L)),   # This is not recursive
            (Interval(20, sys.maxint),  (10L, 10L)),  # This is not recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), (2L, 2L)), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-3" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (10L, 20L)),  # This is not recursive
            (Interval(20, sys.maxint),  (0L, 1L)),    # This is recursive
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), (2L,)), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

