#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, "./")
from   track_analysis_single_pattern                          import choice_str, pattern_db, choice
import quex.engine.state_machine.algorithm.acceptance_pruning as     acceptance_pruning
import help

if "--hwut-info" in sys.argv:
    print "Paths Analysis: Single Pattern;"
    print choice_str
    sys.exit()

acceptance_pruning._deactivated_for_unit_test_f = True

sm = help.prepare(pattern_db[choice])

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm)

