#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.analyzer.core                        import Analyzer
import quex.engine.analyzer.template.core               as     templates 
from   quex.engine.analyzer.template.TEST.templates_aux import *
from   quex.engine.state_machine.core                   import StateMachine
from   quex.blackboard                                  import E_EngineTypes, E_Compression
from   quex.engine.interval_handling                    import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Get Best Matching Pair"
    print "CHOICES: 0, 1, 2, 3, recursive;"
    sys.exit(0)

def test(TriggerMapList):
    sm = StateMachine()

    # The init state cannot be combined, create some dummy after init
    state_index = sm.add_transition(sm.init_state_index, Interval(32))

    for trigger_map in TriggerMapList:
        for info in trigger_map:
            if len(info) == 3:
                sm.add_transition(state_index, Interval(info[0], info[1]), info[2])
            else:
                sm.add_transition(state_index, Interval(info[0]), info[1])
        state_index += 1

    ## print "##sm:", sm
    # Backward analyzers do not consider so much entry and drop-out ...
    analyzer = Analyzer(sm, E_EngineTypes.BACKWARD_PRE_CONTEXT)
    for state in analyzer.state_db.itervalues():
        state.entry.finish(None)

    db = templates.CombinationDB(analyzer, 33, E_Compression.TEMPLATE, analyzer.state_db.keys())

    for element in db.gain_matrix:
        print
        ## print_tm(element[2].transition_map)
        print "Combination: %i & %i"  % (element[0], element[1])
        print_metric(element[2].transition_map)
        print "##Gain:        %i" % element[2].gain

    info = db.pop_best()
    print "Best matching pair: ",
    if info is None: print "None"
    else:            print str(tuple(info.state_index_list)).replace("L", "")

if "0" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 10L),
                (11, 20L),
                (12, 30L),
                (13, 40L),
            ], [
                (10, 11L),
                (11, 21L),
                (12, 31L),
                (13, 41L),
            ]
    ]

elif "1" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 10L),
                (11, 20L),
            ], [
                (10, 11L),
                (11, 30L),
            ], [
                (10, 10L),
                (11, 21L),
            ]
    ]

elif "2" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 10L),
                (11, 20L),
                (12, 30L),
            ], [
                (10, 10L),
                (11, 30L),
                (12, 30L),
                (14, 30L),
            ], [
                (10, 10L),
                (11, 20L),
                (12, 30L),
                (14, 30L),
            ]
    ]

elif "3" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 10L),
            ], [
                (20, 10L),
            ], [
                (30, 10L),
            ]
    ]

elif "recursive" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 1L),  # State 1 --> State 1
            ], [
                (10, 4L),
            ], [
                (10, 3L),  # State 3 --> State 3
            ]
    ]

test(trigger_map_list)
