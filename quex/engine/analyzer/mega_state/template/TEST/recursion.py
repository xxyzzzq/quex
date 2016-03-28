#! /usr/bin/env python
#
# See whether recursion produces correct transition maps. That is, recursion
# to a common door of the template state can only be implemented if:
#
# -- The states trigger on the SAME trigger.
# -- The recursive entry to the states has the SAME command lists.
#
# Any other transition from a state in the template to another state in the
# template may remain targetting the same DoorID.
#
# CHOICES:
#
# Recursion on:
#
#   0:  SAME character to same states with EMPTY command list.
#   0b: DIFFERENT character to same states with EMPTY command list.
#   1:  SAME character to same states with SAME command list.
#   1b: SAME character to same states with DIFFERENT command list.
#   1c: DIFFERENT character to same states with SAME command list.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.engine.state_machine.index                             as index
import quex.engine.analyzer.mega_state.template.core               as templates
from   quex.engine.analyzer.mega_state.template.state              import TemplateState, combine_maps
from   quex.engine.analyzer.state.entry_action                     import TransitionID, \
                                                                          TransitionAction
from   quex.engine.operations.operation_list                       import Op
from   quex.engine.analyzer.mega_state.template.TEST.templates_aux import *

from   quex.engine.misc.interval_handling import *
from   quex.blackboard                    import E_StateIndices, E_R


if "--hwut-info" in sys.argv:
    print "Template states handling recursion;"
    print "CHOICES: 0, 0b, 1, 1b, 1c;"
    sys.exit(0)

def test(analyzer, state_a, state_b, DrawF=True):
    print
    print "(Straight)---------------------------------------"
    combine(analyzer, state_a, state_b, "A", "B", DrawF)
    print "(Vice Versa)-------------------------------------"
    combine(analyzer, state_b, state_a, "A", "B", DrawF)

def recursive_tm(Trigger, StateIndex):
    return [ 
        (Interval(Trigger), long(StateIndex))
    ]

def basic_setup(Triggers):
    state_index_list = [ index.get() for i in xrange(2) ]

    # AnalyzerState-s: The base.
    setup_list = [   
        # StateIndex, TransitionMap
        (long(state_index), recursive_tm(Triggers[i], long(state_index)))
        for i, state_index in enumerate(state_index_list)
    ] 

    analyzer = get_Analyzer(setup_list)

    return analyzer, \
           analyzer.state_db[state_index_list[0]], \
           analyzer.state_db[state_index_list[1]]

def set_recursive_command_list(State, TheOpList):
    State.entry.enter_OpList(State.index, State.index, OpList.from_iterable(TheOpList))
    State.entry.categorize(State.index)

if "0" in sys.argv:
    analyzer, a, b = basic_setup([10, 10]) # Recursion on trigger = 10 in both states

elif "0b" in sys.argv:
    analyzer, a, b = basic_setup([10, 11]) # Recursion on trigger = 10 in a, trigger = 11 in b

elif "1" in sys.argv:
    analyzer, a, b = basic_setup([10, 10]) # Recursion on trigger = 10 in both states
    print "NOTE: Set SAME command list in recursion."
    set_recursive_command_list(a, [ Op.Increment(E_R.InputP) ])
    set_recursive_command_list(b, [ Op.Increment(E_R.InputP) ])
    
elif "1b" in sys.argv:
    analyzer, a, b = basic_setup([10, 10]) # Recursion on trigger = 10 in both states
    print "NOTE: Set DIFFERENT command list in recursion."
    set_recursive_command_list(a, [ Op.Increment(E_R.InputP) ])
    set_recursive_command_list(b, [ Op.Decrement(E_R.InputP) ])
    
elif "1c" in sys.argv:
    analyzer, a, b = basic_setup([10, 11]) # Recursion on trigger = 10 in both states
    print "NOTE: Set SAME command list in recursion ON DIFFERENT triggers."
    set_recursive_command_list(a, [ Op.Increment(E_R.InputP) ])
    set_recursive_command_list(b, [ Op.Increment(E_R.InputP) ])
    
test(analyzer, a, b)
