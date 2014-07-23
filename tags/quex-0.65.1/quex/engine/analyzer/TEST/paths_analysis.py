#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, "./")
from   track_analysis                                         import choice_str, \
                                                                     pattern_list_db, \
                                                                     choice
import quex.engine.state_machine.algorithm.acceptance_pruning as     acceptance_pruning
import help

if "--hwut-info" in sys.argv:
    print "Paths Analyzis: Without Pre- and Post-Contexts;"
    print choice_str
    sys.exit()


sm = help.prepare(pattern_list_db[choice])

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm)
