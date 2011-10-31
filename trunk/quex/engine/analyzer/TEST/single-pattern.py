#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine         as regex
from   quex.engine.generator.base                   import get_combined_state_machine
from   quex.engine.analyzer.core                    import E_InputActions
import quex.engine.state_machine.algorithm.acceptance_pruning as     acceptance_pruning
import quex.engine.analyzer.core                    as core
import help_drawing

if "--hwut-info" in sys.argv:
    print "Single Pattern Checks;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9;"
    sys.exit()

choice = sys.argv[1]

pattern_list = {
    "0": [ 'a/bc',     ],      
    #  ┌────┐  a   ┌────┐  b   ┌────┐  c   ┌────┐
    #  │ 28 │ ───▶ │ 29 │ ───▶ │ 30 │ ───▶ │ 31 │
    #  └────┘      └────┘S     └────┘      └────┘A,R
    #____________________________________________________________________________________

    "1": [ 'a+/bc',     ],     
    #                  a
    #                ┌───┐
    #                ▼   │
    #  ┌────┐  a   ┌───────┐  b   ┌────┐  c   ┌────┐
    #  │ 39 │ ───▶ │  40   │ ───▶ │ 41 │ ───▶ │ 42 │
    #  └────┘      └───────┘S     └────┘      └────┘A,R
    #____________________________________________________________________________________

    "2": [ 'a/bc+',     ],     
    #                                          c
    #                                        ┌───┐
    #                                        ▼   │
    #  ┌────┐  a   ┌────┐  b   ┌────┐  c   ┌───────┐
    #  │ 39 │ ───▶ │ 40 │ ───▶ │ 41 │ ───▶ │  42   │
    #  └────┘      └────┘S     └────┘      └───────┘A,R
    #  
    #____________________________________________________________________________________

    "3": [ '(a+|bc)/d+', ],    
    #                                                   d
    #                                                 ┌───┐
    #                                                 ▼   │
    #        ┌───────┐  b   ┌────┐  c   ┌────┐  d   ┌───────┐
    #    ┌── │  69   │ ───▶ │ 71 │ ───▶ │ 72 │ ───▶ │  73   │
    #    │   └───────┘      └────┘      └────┘S     └───────┘A,R
    #    │       a                                    ▲
    #    │ a   ┌───┐                                  │
    #    │     ▼   │                                  │
    #    │   ┌───────┐  d                             │
    #    └─▶ │  70   │ ───────────────────────────────┘
    #        └───────┘S
    #____________________________________________________________________________________

    "4": [ 'x/a/b',     ],     
    #  ┌────┐  a   ┌────┐  b   ┌────┐
    #  │ 30 │ ───▶ │ 31 │ ───▶ │ 32 │
    #  └────┘      └────┘S     └────┘A,R
    #____________________________________________________________________________________

    "5": [ 'x/(a+|bc)/d+f', ], 
    #                                                   d
    #                                                 ┌───┐
    #                                                 ▼   │
    #        ┌───────┐  b   ┌────┐  c   ┌────┐  d   ┌───────┐  f   ┌────┐
    #    ┌── │  92   │ ───▶ │ 94 │ ───▶ │ 95 │ ───▶ │  96   │ ───▶ │ 97 │
    #    │   └───────┘      └────┘      └────┘S     └───────┘      └────┘A,R
    #    │       a                                    ▲
    #    │ a   ┌───┐                                  │
    #    │     ▼   │                                  │
    #    │   ┌───────┐  d                             │
    #    └─▶ │  93   │ ───────────────────────────────┘
    #        └───────┘S
    #____________________________________________________________________________________

    "6": [ 'a' ],
    #  ┌───┐  a   ┌───┐
    #  │ 7 │ ───▶ │ 8 │
    #  └───┘      └───┘A
    #____________________________________________________________________________________

    "7": [ 'aa?' ],
    #  ┌────┐  a   ┌────┐  a   ┌────┐
    #  │ 16 │ ───▶ │ 17 │ ───▶ │ 18 │
    #  └────┘      └────┘A     └────┘A
    #____________________________________________________________________________________

    "8": [ 'a|(bc)' ],
    #         a
    #    ┌───────────────────────┐
    #    │                       ▼
    #  ┌────┐  b   ┌────┐  c   ┌────┐
    #  │ 34 │ ───▶ │ 36 │ ───▶ │ 35 │
    #  └────┘      └────┘      └────┘A
    #____________________________________________________________________________________

    "9": [ 'a|(a(a|(bc))e)' ],
    #                     a
    #                ┌───────────────────────┐
    #                │                       ▼
    #  ┌────┐  a   ┌────┐  b   ┌────┐  c   ┌────┐  e   ┌────┐
    #  │ 79 │ ───▶ │ 80 │ ───▶ │ 82 │ ───▶ │ 81 │ ───▶ │ 83 │
    #  └────┘      └────┘A     └────┘      └────┘      └────┘A
    #____________________________________________________________________________________
}[choice]

acceptance_pruning._deactivated_for_unit_test_f = True
state_machine_list = map(lambda x: regex.do(x, {}).sm, pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm  = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=True)
# print sm.get_string(NormalizeF=False)

analyzer = core.do(sm)

for state in analyzer:
    if state.index == sm.init_state_index: 
        assert state.input == E_InputActions.DEREF
    else:
        assert state.input == E_InputActions.INCREMENT_THEN_DEREF
    print state.get_string(InputF=False, TransitionMapF=False)
