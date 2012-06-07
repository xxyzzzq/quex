#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.index                             as index
import quex.engine.analyzer.mega_state.template.core               as templates
from   quex.engine.analyzer.mega_state.template.state              import TemplateState, combine_maps, MegaState_Target
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *

from   quex.engine.interval_handling import *
from   quex.blackboard               import E_StateIndices


if "--hwut-info" in sys.argv:
    print "Combine Simple"
    print "CHOICES: plain, recursive, distinguished;"
    sys.exit(0)

def print_tm(TM):
    for interval, target in TM:
        if   isinstance(target, (int, long)) \
           or isinstance(target, MegaState_Target) and not target.drop_out_f:
            print "(%s, %s), " % (interval, repr(target).replace("MegaState_Target", "MST")),
        else:
            print "%s " % repr(target).replace("MegaState_Target", "MST"),
    print

def combine_states(A, B):
    global state_list
    global analyzer
    print "----------------------------------------------------------"
    print "State%i: " % A,
    print_tm(state_list[A].transition_map)
    print "State%i: " % B,
    print_tm(state_list[B].transition_map)

    result = TemplateState(state_list[A], state_list[B], analyzer)
    for state_index in result.implemented_state_index_list():
        analyzer.state_db[state_index] = AbsorbedState(analyzer.state_db[state_index], 
                                                       result)
    result.finalize_transition_map(analyzer.state_db)

    state_list.append(result)
    result_state_index = len(state_list) - 1
    print "State%i = Template(State%i + State%i)" % (result_state_index, A, B)
    print "        ",
    print_tm(result.transition_map)
    print "official template state index:", result.index
    #print "DoorReplacementDB:"
    #for old, new in sorted(result.door_id_replacement_db.iteritems(), 
    #                       key=lambda x: (x[0].state_index, x[0].door_index)):
    #    print "    %s -> %s" % (old, new)
    #print
    print "door tree root:"
    print result.entry.door_tree_root.get_string(result.entry.transition_db)
    return result_state_index

if "plain" in sys.argv:
    TM = [ 
           (Interval(10, 11), 1L),
         ]

    state_list, analyzer = setup_AnalyzerStates([(index.get(), TM), (index.get(), TM), (index.get(), TM), (index.get(), TM), (index.get(), TM)])

elif "recursive" in sys.argv:
    setup_list = []
    for i in xrange(5):
        state_index = index.get()
        tm = [(Interval(10, 11), state_index)] 
        setup_list.append((state_index, tm))

    state_list, analyzer = setup_AnalyzerStates(setup_list)

elif "distinguished" in sys.argv:
    setup_list = []
    for i in xrange(5):
        state_index = index.get()
        tm = [(Interval(10, 11), 1000 + 1000 * state_index)] 
        setup_list.append((state_index, tm))

    state_list, analyzer = setup_AnalyzerStates(setup_list)

t01       = test_combination(state_list[0], state_list[1], analyzer, StateA_Name="0",              StateB_Name="1")
t23       = test_combination(state_list[2], state_list[3], analyzer, StateA_Name="2",              StateB_Name="3")
t_01_23   = test_combination(t01,           t23,           analyzer, StateA_Name="%i" % t01.index, StateB_Name="%i" % t23.index)
t_01_23_4 = test_combination(state_list[4], t_01_23,       analyzer, StateA_Name="4",              StateB_Name="%i" % t01.index)

