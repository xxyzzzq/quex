#! /usr/bin/env python
#
# NOTE: Recursion is not considered during measurement. See note in README.txt.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
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
    print "CHOICES: 1, 2;"
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


