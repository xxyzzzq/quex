#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.blackboard                       import E_InputActions
from   quex.engine.analyzer.position_register_map import print_this
import help

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Special Loops and Forks"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7;"
    sys.exit()

if "0" in sys.argv:
    pattern_list = [
         "aa(((b000)|(b111))+)*cc",
         "aa(((b000)|(b111))*)b0", 
         "aa(((b000)|(b111))*)b1", 
         "a"                      
    ]
    #      ┌────┐  a   ┌───*┐  a   ┌────┐  c   ┌────┐  c   ┌───*┐
    #      │ 0  │ ───▶ │ 1  │ ───▶ │ 2  │ ───▶ │ 8  │ ───▶ │ 9  │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                      A133    / |  \                      A55
    #                             /  |   \                  
    #       1┌────────▶──────────+   | b  +───────────◀──────┐0
    #        |                       ▼                       |
    #      ┌────┐  1   ┌───*┐  1   ┌────┐  0   ┌───*┐  0   ┌────┐
    #      │ 7  │ ◀─── │ 6  │ ◀─── │ 3  │ ───▶ │ 4  │ ───▶ │ 5  │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                      A131                    A88
    #____________________________________________________________________

elif "1" in sys.argv:
    pattern_list = [
         "0/aa(((b000)|(b111))+)*cc/",
         "1/aa(((b000)|(b111))*)b0/", 
         "2/aa(((b000)|(b111))*)b1/", 
         "3/a/"                      
    ]
    #
    # path: [0, 1, 2, 3, 4, 5, 2, 3, 6, 7, 2, 3, 6, 7, 2]
    #       Is the proof that we need to store input positions in 
    #       separate registers. Even if on the first glance the positions
    #       for what is stored in 4 and 6 is only two positions away.
    #
    #      ┌────┐  a   ┌───*┐  a   ┌────┐  c   ┌────┐  c   ┌───*┐
    #      │ 0  │ ───▶ │ 1  │ ───▶ │ 2  │ ───▶ │ 8  │ ───▶ │ 9  │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                      A133    / |  \                      A55
    #                             /  |   \                  
    #       1┌────────▶──────────+   | b  +───────────◀──────┐0
    #        |                       ▼                       |
    #      ┌────┐  1   ┌───*┐  1   ┌────┐  0   ┌───*┐  0   ┌────┐
    #      │ 7  │ ◀─── │ 6  │ ◀─── │ 3  │ ───▶ │ 4  │ ───▶ │ 5  │
    #      └────┘      └────┘      └────┘      └────┘      └────┘
    #                      A131                    A88
    #____________________________________________________________________

elif "2" in sys.argv:
    pattern_list = [
            "(a)|(abc*de)|(abc*defg)",
    ]

elif "3" in sys.argv:
    pattern_list = [
            "0/(a)|(abc*de)|(abc*defg)/",
            "1/(a)|(abc*de)|(abc*defg)/",
    ]

elif "4" in sys.argv:
    pattern_list = [
            "a(b(c(c(cd)*d)*d)*e(fg)?)?"
    ]
elif "5" in sys.argv:
    pattern_list = [
        "0/(bc)|(d)/",
        "1/(b)|(de)/",
        "((bc)|(de))fgh",
    ]
elif "6" in sys.argv:
    pattern_list = [
        "0/(b+c+)|(d+)/",
        "1/(b+)|(d+e+)/",
        "((b+c+)|(d+e+))fgh",
    ]
elif "7" in sys.argv:
    pattern_list = [
        "0/(bc)|(d)/",
        "1/(b)|(de)/",
        "((bc)|(de))f+gh",
    ]
else:
    assert False


sm = help.prepare(pattern_list)

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm, PrintPRM_F=True)
