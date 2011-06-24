#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core
from   quex.engine.analyzer.core                 import InputActions
from   quex.blackboard                           import EngineTypes
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

state_machine_list = map(lambda x: 
                         regex.do(x, {}).core().pre_context_sm(), 
                         pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

# For DEBUG purposes: specify 'DRAW' on command line
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.Analyzer(sm, EngineTypes.BACKWARD_PRE_CONTEXT)

for state in analyzer:
    assert state.input == InputActions.DECREMENT_THEN_DEREF
    print state.get_string(InputF=False, TransitionMapF=False)
