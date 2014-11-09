#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.analyzer.core                        import Analyzer
import quex.engine.analyzer.mega_state.template.core    as     templates 
from   quex.engine.analyzer.mega_state.template.state   import TemplateState
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *
from   quex.engine.state_machine.core                   import StateMachine
import quex.engine.analyzer.engine_supply_factory       as     engine
from   quex.blackboard                                  import E_Compression
from   quex.engine.misc.interval_handling                    import *


if "--hwut-info" in sys.argv:
    print "Transition Map Templates: Get Best Matching Pair"
    print "CHOICES: 0, 1, 2, 3, recursive;"
    sys.exit(0)

def my_setup(TriggerMapList):
    def adapt(Info):
        trigger, target_state = Info
        return (Interval(trigger), target_state)
    
    def adapt_tm(tm):
        return [ adapt(x) for x in tm ]

    setup_list = [
        (long(i), adapt_tm(tm))
        for i, tm in enumerate(TriggerMapList)
    ]
    return get_Analyzer(setup_list), \
           [state_index for state_index, trigger_map in setup_list]

def test(TriggerMapList):
    analyzer, \
    state_index_list = my_setup(TriggerMapList) 

    elect_db         = templates.ElectDB(analyzer, state_index_list)
    candidate_list   = templates.CandidateList(elect_db, False, 0)

    print "Gain Matrix (%i elements)" % len(candidate_list)
    print "State0  State1 Gain"
    for element in candidate_list:
        print "%i      %i      %i" % (element.state_a.index, element.state_b.index, element.gain)
    print

    elect = candidate_list.pop_best()
    print "Best matching pair: ",
    if elect is None: 
        print "None"
    else:            
        best = TemplateState(elect)
        print str(tuple(best.state_index_sequence())).replace("L", "")

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
