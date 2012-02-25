#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.analyzer.template.core               as templates
from   quex.engine.analyzer.template.state              import combine_maps, TemplateState
from   quex.engine.analyzer.template.TEST.templates_aux import *

from   quex.engine.interval_handling import *

if "--hwut-info" in sys.argv:
    print "Combination of Two Transition Maps"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TMa, TMb, InvolvedStateListA=[10L], InvolvedStateListB=[20L], DrawF=False):

    StateList, analyzer = setup_AnalyzerStates([(InvolvedStateListA[0], TMa), 
                                                (InvolvedStateListB[0], TMb)])
    StateA, StateB = StateList

    if DrawF:
        print "DoorTree(A):"
        print "    " + StateA.entry.door_tree_root.get_string(StateA.entry.transition_db).replace("\n", "\n    ")
        print "DoorTree(B):"
        print "    " + StateB.entry.door_tree_root.get_string(StateB.entry.transition_db).replace("\n", "\n    ")

    print "(Straight)---------------------------------------"
    test_combination(StateA, StateB, analyzer, DrawF)
    print
    print "(Vice Versa)-------------------------------------"
    test_combination(StateB, StateA, analyzer, DrawF)

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
            (Interval(5, 20),           3L),
            (Interval(20, 25),          4L),
            (Interval(25, 35),          5L),
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
    test(tm0, tm1, [1L], [2L], DrawF=True)
#    Today, I would say that the comment below is utter nonsense: <fschaef>
#    print "A target combination (1L, 2L) and vice versa has not to appear,"
#    print "because this would mean recursion and is thus an equivalence."

elif "recursive-b" in sys.argv:
    pass
#    We no longer distinguish between uniform entries for computation of combination maps.
#
#    print "Involved states in First = 1L"
#    print "Involved states in Second = 2L"
#    print "=> when First triggers to 1L and Second to 2L, then both"
#    print "   are recursive and no distinction needs to be made."
#    print "BUT: HERE STATE ENTRIES ARE NOT UNIFORM --> NO RECURSION DETECTION"
#    tm1 = [ 
#            (Interval(-sys.maxint, sys.maxint), 2L),
#          ]
#    test(tm0, tm1, [1L], [2L])

