#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
from   quex.engine.analyzer.core             import E_InputActions
import quex.engine.analyzer.core             as core
import help

if "--hwut-info" in sys.argv:
    print "Track Analyzis: With Pre-Contexts;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11;"
    sys.exit()

if "0" in sys.argv:
    pattern_list = [
        'x/a/',        
        'ab',     
    ]
elif "1" in sys.argv:
    pattern_list = [
        'ab',     
        'x/a/',        
    ]
elif "2" in sys.argv:
    pattern_list = [
        'x/a/',        
        'abc',        
    ]
elif "3" in sys.argv:
    pattern_list = [
        'abc',        
        'x/a/',        
    ]
elif "4" in sys.argv:
    pattern_list = [
        'a',        
        'x/abc/'
    ]
elif "5" in sys.argv:
    pattern_list = [
        'a',
        'x/a/',
        'x/ab/',
        'x/abc/',
    ]
elif "6" in sys.argv:
    pattern_list = [
        'a',
        'b',
        'x/abc/',
        'x/bbc/',
    ]
elif "7" in sys.argv:
    pattern_list = [
        '^[ab]',        
        '((ab)|b)cd',
    ]
elif "8" in sys.argv:
    pattern_list = [
        '^a',        
        '^b',        
        '((ab)|b)cd',
    ]
elif "9" in sys.argv:
    pattern_list = [
        '^a',        
        'b',        
        '((ab)|b)cd',
    ]
elif "10" in sys.argv:
    # Non-uniform traces with multiple pre-contexts
    pattern_list = [
        'x/a+/',
        'x/b/',
        '(a+|bc+)de',
        '0/(a+|bc+)def/',
        '1/(a+|bc+)def/',
        '2/(a+|bc+)def/',
    ]
elif "11" in sys.argv:
    # Non-uniform traces with multiple pre-contexts
    pattern_list = [
        'x/a/',
        'x/b/',
        '0/(a|bb?c?)de/',
        '1/(a|bb?c?)de/',
        '2/(a|bb?c?)de/',
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}).sm, pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm  = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.do(sm)

for state in analyzer:
    if state.index == sm.init_state_index: 
        assert state.input == E_InputActions.DEREF
    else:
        assert state.input == E_InputActions.INCREMENT_THEN_DEREF
    print state.get_string(InputF=False, TransitionMapF=False)
