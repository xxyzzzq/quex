#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.index                             as index
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

t01       = test_combination(state_list[0], state_list[1], analyzer, StateA_Name="0",              StateB_Name="1", DrawF=True, FinalizeF=False)
t23       = test_combination(state_list[2], state_list[3], analyzer, StateA_Name="2",              StateB_Name="3", DrawF=True, FinalizeF=False)
t_01_23   = test_combination(t01,           t23,           analyzer, StateA_Name="%i" % t01.index, StateB_Name="%i" % t23.index, DrawF=True, FinalizeF=False)
t_01_23_4 = test_combination(state_list[4], t_01_23,       analyzer, StateA_Name="4",              StateB_Name="%i" % t01.index, DrawF=True, FinalizeF=True)

