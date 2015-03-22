#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.index                             as     sm_index
from   quex.engine.analyzer.state.core                             import AnalyzerState
from   quex.engine.analyzer.transition_map                         import TransitionMap
import quex.engine.analyzer.mega_state.template.core               as     templates
from   quex.engine.analyzer.mega_state.template.state              import combine_maps, TemplateState
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *
import quex.engine.operations.tree                 as     entry_door_tree

from   quex.engine.misc.interval_handling import *

if "--hwut-info" in sys.argv:
    print "Combination of Two Transition Maps"
    print "CHOICES: 1, 2, 2b, 3, 4;" 
    sys.exit(0)

def test(TMa, TMb, InvolvedStateListA=[10L], InvolvedStateListB=[20L], DrawF=False):

    analyzer = setup_AnalyzerStates([(InvolvedStateListA[0], TMa), 
                                     (InvolvedStateListB[0], TMb)])
    StateA = analyzer.state_db[InvolvedStateListA[0]]
    StateB = analyzer.state_db[InvolvedStateListB[0]]

    if DrawF:
        print "DoorTree(A):"
        # StateA.entry.categorize()
        door_tree_root = entry_door_tree.do(StateA.index, StateA.entry)
        print "    " + door_tree_root.get_string(StateA.entry).replace("\n", "\n    ")

        #StateB.entry.categorize()
        door_tree_root = entry_door_tree.do(StateB.index, StateB.entry)
        print "DoorTree(B):"
        print "    " + door_tree_root.get_string(StateB.entry).replace("\n", "\n    ")

    print "(Straight)---------------------------------------"
    test_combination(StateA, StateB, analyzer, "A", "B", DrawF)
    print
    print "(Vice Versa)-------------------------------------"
    test_combination(StateB, StateA, analyzer, "A", "B", DrawF)

def get_transition_map(TM, StateIndex, DropOutCatcher=None):
    if DropOutCatcher is None:
        DropOutCatcher = AnalyzerState(sm_index.get(), TransitionMap())

    def get_door_id(Target):
        return DoorID(Target, 0)
    tm = TransitionMap.from_iterable(TM, get_door_id)
    return tm.relate_to_TargetByStateKeys(StateIndex, DropOutCatcher)

def test_core(tm_a, tm_b):
    result, scheme_n = combine_maps(tm_a, tm_b)
    print result.get_string(Option="hex").replace("TargetByStateKey:", "*")

def test(TMA, TMB):
    tm_a = get_transition_map(TMA, 1L)
    tm_b = get_transition_map(TMB, 2L)
    print "TargetMap A:"
    print tm_a.get_string(Option="hex").replace("TargetByStateKey:", "*")
    print "TargetMap B:"
    print tm_b.get_string(Option="hex").replace("TargetByStateKey:", "*")
    print "Combined (A,B):"
    test_core(tm_a, tm_b)
    print "Combined (B,A):"
    test_core(tm_b, tm_a)

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

# "recursiveness falls into the domain of 'categorize' 'assign DoorIDs.
# This is no longer handled in this test!
# elif "recursive" in sys.argv:
#     print "Involved states in First = 1L"
#     print "Involved states in Second = 2L"
#     print "=> when First triggers to 1L and Second to 2L, then both"
#     print "   are recursive and no distinction needs to be made."
#     tm1 = [ 
#             (Interval(-sys.maxint, sys.maxint), 2L),
#           ]
#     test(tm0, tm1) # , [1L], [2L], DrawF=True)
#    Today, I would say that the comment below is utter nonsense: <fschaef>
#    print "A target combination (1L, 2L) and vice versa has not to appear,"
#    print "because this would mean recursion and is thus an equivalence."

# elif "recursive-b" in sys.argv:
#     pass
# #    We no longer distinguish between uniform entries for computation of combination maps.
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

