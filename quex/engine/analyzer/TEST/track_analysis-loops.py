#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
from   quex.engine.analyzer.core             import E_InputActions
from   quex.engine.analyzer.position_register_map import print_this
import quex.engine.analyzer.core             as core
import help

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Without Pre- and Post-Contexts;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9;"
    sys.exit()

if "0" in sys.argv:
    pattern_list = [
         "aa(((b000)|(b111))+)*cc",
         "aa(((b000)|(b111))*)b0", 
         "aa(((b000)|(b111))*)b1", 
         "a"                      
    ]
    #      ┌────┐  a   ┌───*┐  a   ┌────┐  c   ┌────┐  c   ┌───*┐
    #      │ 0  │ ───▶ │ 1  │ ───▶ │ 2  │ ───▶ │ 27 │ ───▶ │ 28 │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                             /  |   \                  
    #       1┌───────────────────+   | b  +──────────────────┐0
    #        |                       ▼                       |
    #      ┌────┐  1   ┌───*┐  1   ┌────┐  0   ┌───*┐  0   ┌────┐
    #      │ 9  │ ◀─── │ 8  │ ◀─── │ 3  │ ───▶ │ 4  │ ───▶ │ 5  │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                               
    #____________________________________________________________________


else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}).sm, pattern_list)

sm = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm, PrintPRM_F=True)
