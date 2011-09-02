#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core
from   quex.engine.analyzer.core                 import E_InputActions
from   quex.engine.state_machine.state_core_info import E_EngineTypes
import help_drawing

from   operator import attrgetter

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Backward Input Position Detection;"
    sys.exit()

# There are no 'special cases'
pattern_list = [
    'ax',        
]

state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)
sm                 = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm                 = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line (in sys.argv)
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.do(sm, E_EngineTypes.BACKWARD_INPUT_POSITION)

for state in sorted(analyzer, key=attrgetter("index")):
    assert state.input == E_InputActions.DECREMENT_THEN_DEREF
    print state.get_string(InputF=False, TransitionMapF=False)
