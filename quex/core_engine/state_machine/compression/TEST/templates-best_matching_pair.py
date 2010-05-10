#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.templates as templates 
from   quex.core_engine.state_machine.core import StateMachine
from   quex.core_engine.state_machine.compression.TEST.templates_aux import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Get Best Matching Pair"
    print "CHOICES: 1, 2, 2b, 3, 4, recursive;"
    sys.exit(0)

def test(TriggerMapList):
    sm = StateMachine()
    state_index = sm.init_state_index
    for trigger_map in TriggerMapList:
        for info in trigger_map:
            if len(info) == 3:
                sm.add_transition(state_index, Interval(info[0], info[1]), info[2])
            else:
                sm.add_transition(state_index, Interval(info[0]), info[1])
        state_index += 1

    db = templates.TriggerMapDB(sm)

    print "Best matching pair: ", db.get_best_matching_pair()


if "0" in sys.argv:
    trigger_map_list = [
            [ 
                (10, 10L),
                (11, 30L),
            ], [
                (10, 11L),
                (11, 21L),
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

test(trigger_map_list)
