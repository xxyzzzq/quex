#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.engine.analyzer.template.combine_maps       as combine_maps
import quex.engine.analyzer.template.core               as templates
from   quex.engine.analyzer.template.state              import TemplateState
from   quex.engine.analyzer.template.TEST.templates_aux import *

from   quex.engine.interval_handling import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Combine Combined Trigger Maps"
    print "CHOICES: 1, 2, recursive, recursive-2, recursive-3;"
    sys.exit(0)

class TestTemplateState(TemplateState):
    def __init__(self, TriggerMap, StateIndexList):
        self.__transition_map = TriggerMap
        self.__state_index_list = StateIndexList

    @property 
    def transition_map(self): return self.__transition_map
    @property
    def state_index_list(self): return self.__state_index_list

class TestState:
    def __init__(self, TM, Index=None, StateIndexList=None):
        self.transition_map = TM
        self.index          = Index
        self.state_index_list = StateIndexList

def test(TriggerMapA, StateN_A, TriggerMapB, StateN_B, DoNotMakeCombinationF=True):
    StateListA = range(10, 10 + StateN_A)
    if StateN_A > 1: CombinationA = TestTemplateState(TriggerMapA, StateListA)
    else:            CombinationA = TestState(TriggerMapA, 10)

    StateListB = range(20, 20 + StateN_B)
    if StateN_B > 1: CombinationB = TestTemplateState(TriggerMapB, StateListB)
    else:            CombinationB = TestState(TriggerMapB, 20)

    print
    print "(Straight)---------------------------------------"
    print
    print_tm(TriggerMapA)
    print_tm(TriggerMapB)
    print
    result = combine_maps.do(CombinationA, CombinationB)
    print_tm(result)
    print
    print "(Vice Versa)-------------------------------------"
    print
    print_tm(TriggerMapB)
    print_tm(TriggerMapA)
    print
    result = combine_maps.do(CombinationB, CombinationA)
    print_tm(result)
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

