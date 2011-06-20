#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core
import help_drawing

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Backwards - For Pre-Context;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6;"
    sys.exit()

if "0" in sys.argv:
    """
    ╔════╗  a   ╔════╗  b   ╔════╗
    ║ 26 ║ ───▶ ║ 27 ║ ───▶ ║ 28 ║
    ╚════╝      ╚════╝      ╚════╝
    """
    pattern_list = [
        'x/a/',        
        'y/a/',     
    ]
elif "1" in sys.argv:
    pattern_list = [
        '0yx+/a/',        
        '1yx+/a/',     
    ]
elif "2" in sys.argv:
    pattern_list = [
        'a',        
        'b',     
        '[ab]c'
    ]
elif "3" in sys.argv:
    pattern_list = [
        'a',        
        'b',     
        '[ab]cd'
    ]
elif "4" in sys.argv:
    pattern_list = [
        'aa?',        
        'aa?cd'
    ]
elif "5" in sys.argv:
    pattern_list = [
        '[ab]',        
        '((aa?)|b)cd'
    ]
elif "6" in sys.argv:
    pattern_list = [
        '[ab]',        
        '((ab)|b)cd',
    ]
else:
    assert False


print map(lambda x: regex.do(x, {}), pattern_list)
state_machine_list = map(lambda x: 
                         regex.do(x, {}).core().pre_context_sm(), 
                         pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

# For DEBUG purposes: specify 'DRAW' on command line
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.Analyzer(sm, ForwardF=False)

for state in analyzer:
    assert state.input.move_input_position() == -1   # backwards always
    print state.get_string(InputF=False, TransitionMapF=False)
