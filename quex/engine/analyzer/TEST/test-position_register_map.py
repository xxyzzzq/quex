#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine       as regex
import quex.engine.analyzer.core                  as core
import quex.engine.analyzer.position_register_map as position_register_map
from   quex.engine.generator.base                 import get_combined_state_machine
from   quex.engine.analyzer.core                  import InputActions
from   quex.engine.state_machine.state_core_info  import EngineTypes
import help_drawing

if "--hwut-info" in sys.argv:
    print "Position Register vs. Post-Context and Last Acceptance"
    print "CHOICES: 0, 1, 2, 3;"
    sys.exit()


if "0" in sys.argv:
    print "No Post Context at all"
    print "(no output is good output)"
    pattern_list = [
        'a',        
    ]
elif "1" in sys.argv:
    print "Last Acceptance / Post-Context-ID 'None'"
    pattern_list = [
        'a+',        
        '[ab]+cd',        
    ]
elif "2" in sys.argv:
    print "All Post-Contexts are Combinable"
    pattern_list = [
        'a+',        
        '[ab]+cd',        
        'c/y+z',
        'd/y+z',
        'e/y+z',
    ]
elif "3" in sys.argv:
    print "Two Registers"
    pattern_list = [
        'a+',        
        '[ab]+cd',        
        'a/c/y+z',
        'b/c/y+z',
    ]
elif "4" in sys.argv:
    print "All store at the same state => use same register."
    pattern_list = [
        'a/c/a+z',
        'b/c/a+z',
        'c/c/a+z',
        'd/c/a+z',
    ]
elif "5" in sys.argv:
    print "12 Cases store at 4 places => 4 registers."
    pattern_list = [
        'a/c/a+z',
        'b/c/a+z',

        'a/c|cb/a+z',
        'b/c|cb/a+z',

        'a/c|cba/a+z',
        'b/c|cba/a+z',

        'a/c|cbaz/a+z',
        'b/c|cbaz/a+z',
    ]
else:
    assert False

state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)
sm                 = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

# For DEBUG purposes: specify 'DRAW' on command line (in sys.argv)
help_drawing.if_DRAW_in_sys_argv(sm)

analyzer = core.Analyzer(sm, EngineTypes.FORWARD)

for state in analyzer:
    print state.get_string(InputF=False, TransitionMapF=False)

for post_context_id, array_index in position_register_map.do(analyzer).iteritems():
    print "   %s: %i" % (repr(post_context_id), array_index)
