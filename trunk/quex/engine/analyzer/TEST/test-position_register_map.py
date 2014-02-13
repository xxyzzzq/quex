#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine       as regex
import quex.engine.analyzer.core                  as core
import quex.engine.analyzer.position_register_map as position_register_map
import quex.engine.analyzer.engine_supply_factory as     engine
from   quex.blackboard                            import  E_TransitionN
from   operator import itemgetter
import help

if "--hwut-info" in sys.argv:
    print "Position Register vs. Post-Context and Last Acceptance"
    print "CHOICES: 0, 1, 2, 3, 4, 5;"
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
        'a/y+z',
        'b/y+z',
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
        '0/c/a+z',
        '1/c/a+z',

        '2/c|cb/a+z',
        '3/c|cb/a+z',

        'a/c|cba/a+z',
        'b/c|cba/a+z',

        'a/c|cbaz/a+z',
        'b/c|cbaz/a+z',
    ]
else:
    assert False

sm = help.prepare(pattern_list)

print "State Machine _____________________________________"
print sm.get_string(OriginalStatesF=False)

# For DEBUG purposes: specify 'DRAW' on command line (in sys.argv)
help.if_DRAW_in_sys_argv(sm)

analyzer = core.Analyzer(sm, engine.FORWARD)

print "Positioning Info __________________________________"
position_register_map.print_this(analyzer)

for post_context_id, array_index in sorted(analyzer.position_register_map.iteritems()):
    print "   %s: %i" % (repr(post_context_id), array_index)
