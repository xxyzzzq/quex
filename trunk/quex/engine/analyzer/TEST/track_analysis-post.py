#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine         as regex
from   quex.engine.generator.base                   import get_combined_state_machine
import quex.engine.analyzer.core                    as core
import quex.engine.state_machine.algorithm.acceptance_pruning as     acceptance_pruning
from   quex.blackboard                              import E_InputActions
import help

if "--hwut-info" in sys.argv:
    print "Track Analyzis: With Post-Contexts;"
    print "CHOICES: 3, 4, 5, 6, 7, 8, 9, 10;"
    sys.exit()

if   "3" in sys.argv:
    pattern_list = [
        'a/b+d',     
        'a/b+e',     
    ]
elif "4" in sys.argv:
    pattern_list = [
        'a/bc',     
        'b/bc',     
        'cbc',
    ]
elif "5" in sys.argv:
    pattern_list = [
        'ab/c',     
        'a/bc',     
        '[ab]bc',
    ]
elif "6" in sys.argv:
    pattern_list = [
        '[ab]bc',
        'ab/c',     
        'a/bc',     
    ]
elif "7" in sys.argv:
    pattern_list = [
        'abc',
        'ab/cde',     
    ]
elif "8" in sys.argv:
    # Case where the acceptance decides about positioning
    #                                       b
    #      ┌───────────────┐              ┌───┐
    #      │               │              ▼   │
    #      │  ┌───┐  x   ┌───────┐  b   ┌───────┐  c   ┌───┐  d   ┌───┐  e   ┌───┐
    #      │  │ 0 │ ───▶ │   1   │ ───▶ │   6*  │ ───▶ │ 3 │ ───▶ │ 4 │ ───▶ │ 5*│
    #      │  └───┘      └───────┘S8    └───────┘R17   └───┘      └───┘      └───┘A44
    #      │                      S17                    ▲                          
    #      │                 a                           │
    #      │               ┌───┐                         │
    #      │               ▼   │                         │
    #      │        a    ┌───────┐  c                    │
    #      └───────────▶ │   2*  │───────────────────────┘
    #                    └───────┘R8
    #____________________________________________________________________
    pattern_list = [
        'x/a+',
        'x/b+',
        'x(a+|b+)cde',
    ]
elif "9" in sys.argv:
    # Case where the acceptance decides about positioning
    pattern_list = [
        'x/ya',
        'xy/b',
        'xy(a|b)cde',
    ]
elif "10" in sys.argv:
    # Case where the acceptance decides about positioning
    pattern_list = [
        'x/ya+',
        'xy/b',
        'xy(a+|b)cde',
    ]
#elif "11" in sys.argv:
#    # Case where the acceptance decides about positioning
#    pattern_list = [
#        "b/[ ]*[cdef]",
#        "ab*/cd?",
#        "a/b*ce?",
#    ]
else:
    assert False


acceptance_pruning._deactivated_for_unit_test_f = True
sm = help.prepare(pattern_list)

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm)
