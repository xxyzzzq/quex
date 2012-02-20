#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.index                  as index
import quex.engine.analyzer.template.core               as templates
from   quex.engine.analyzer.template.state              import TemplateState, combine_maps
from   quex.engine.analyzer.template.TEST.templates_aux import *

from   quex.engine.interval_handling import *
from   quex.blackboard               import E_StateIndices


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Combine Combined Trigger Maps"
    print "CHOICES: 1, 2, recursive, recursive-2, recursive-3, recursive-b, recursive-2b, recursive-3b;"
    sys.exit(0)

def get_TemplateState(analyzer, StateIndexList):
    assert len(StateIndexList) > 1

    result = TemplateState(analyzer.state_db[StateIndexList[0]], 
                           analyzer.state_db[StateIndexList[1]], 
                           analyzer)
    for i in StateIndexList[2:]:
        result = TemplateState(result, analyzer.state_db[i], 
                               analyzer)
    return result

def test(TriggerMapA, StateN_A, TriggerMapB, StateN_B):
    state_setup = []
    StateListA = [ long(i) for i in xrange(StateN_A) ]
    StateListB = [ long(i) for i in xrange(StateN_A, StateN_A + StateN_B) ]
    def extract_transition_map(XTM, Index):
        result = []
        for interval, specification in XTM:
            result.append((interval, specification[Index]))
        return result

    state_setup.extend([ (index.get(), extract_transition_map(TriggerMapA, i)) for i, state_index in enumerate(StateListA)])
    state_setup.extend([ (index.get(), extract_transition_map(TriggerMapB, i)) for i, state_index in enumerate(StateListB)])

    state_list, analyzer = setup_AnalyzerStates(state_setup)
    if StateN_A == 1: state_a = analyzer.state_db[StateListA[0]] # Normal AnalyzerState
    else:             state_a = get_TemplateState(analyzer, StateListA)
    if StateN_B == 1: state_b = analyzer.state_db[StateListB[0]] # Normal AnalyzerState
    else:             state_b = get_TemplateState(analyzer, StateListB)

    print
    print "(Straight)---------------------------------------"
    print
    print "States: %s" % StateListA
    print_tm(state_a.transition_map)
    print "States: %s" % StateListB
    print_tm(state_b.transition_map)
    print
    result = TemplateState(state_a, state_b, analyzer)
    print_tm(result.transition_map)
    print
    print "(Vice Versa)-------------------------------------"
    print
    print "States: %s" % StateListB
    print_tm(state_b.transition_map)
    print "States: %s" % StateListA
    print_tm(state_a.transition_map)
    print
    result = TemplateState(state_b, state_a, analyzer)
    print_tm(result.transition_map)
    print

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
    test(tm0, 3, tm1, 3)

elif "2" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, 10), (100L, 200L, 300L)),
            (Interval(10, 20),          (200L, 100L, 100L)),
            (Interval(20, 30),          (300L, 400L, 500L)),
            (Interval(30, sys.maxint),  (200L, 100L, 100L)),
          ]
    test(tm0, 3, tm1, 3)

elif "recursive" in sys.argv:
    tm1 = [ 
            # Recursion in states 0, 1, 2
            (Interval(-sys.maxint, sys.maxint), (0L, 1L, 2L)),  
          ]
    test(tm0, 3, tm1, 3)

elif "recursive-2" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (1L, 2L)),    # This is not recursive
            (Interval(20, sys.maxint),  10L),         # This is not recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-3" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (1L, 2L)),    # This is not recursive
            (Interval(20, sys.maxint),  E_StateIndices.RECURSIVE), 
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-b" in sys.argv:
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), E_StateIndices.RECURSIVE),
          ]
    test(tm0, 3, tm1, 3)

elif "recursive-2b" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (1L, 2L)),    # This is not recursive
            (Interval(20, sys.maxint),  10L),         # This is not recursive!
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

elif "recursive-3b" in sys.argv:
    tm0 = [ 
            (Interval(-sys.maxint, 20), (1L, 2L)),    # This is not recursive
            (Interval(20, sys.maxint),  E_StateIndices.RECURSIVE), 
          ]
    tm1 = [ 
            (Interval(-sys.maxint, sys.maxint), 20L), # This is recursive!
          ]
    test(tm0, 2, tm1, 1)

