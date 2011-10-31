#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
import quex.engine.state_machine.acceptance_pruning as     acceptance_pruning
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core
from   quex.blackboard                       import E_InputActions, \
                                                    E_EngineTypes
import help_drawing

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Backwards - For Pre-Context;"
    print "CHOICES: 0, 1;"
    sys.exit()

if "0" in sys.argv:
    pattern_list = [
        'x/a/',        
        'y/a/',     
    ]
elif "1" in sys.argv:
    pattern_list = [
        'x+/a/',        
        'yx+/a/',     
    ]
else:
    assert False

acceptance_pruning._deactivated_for_unit_test_f = True
state_machine_list = map(lambda x: 
                         regex.do(x, {}).inverse_pre_context_sm, 
                         pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm  = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.do(sm, E_EngineTypes.BACKWARD_PRE_CONTEXT)

for state in analyzer:
    assert state.input == E_InputActions.DECREMENT_THEN_DEREF
    print state.get_string(InputF=False, TransitionMapF=False)
