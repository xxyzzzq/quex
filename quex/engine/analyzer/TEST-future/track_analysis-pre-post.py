#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core

if "--hwut-info" in sys.argv:
    print "Track Analyzis: With Pre- and Post-Contexts;"
    print "CHOICES: 0, 1, 2, 3;"
    sys.exit()

if   "0" in sys.argv:
    pattern_list = [
        'x/a/b',     
    ]
elif "1" in sys.argv:
    pattern_list = [
        'x/a/bc',
        'y/ab/c',
        'z/abc/',
    ]
elif "2" in sys.argv:
    pattern_list = [
        'x/a/',        
        'a/bc',        
        'a/bcde',        
        'a',
    ]
elif "3" in sys.argv:
    pattern_list = [
        'x/a/',        
        'a/b+c',        
        'a/bcde',        
        'a',
    ]
elif "4" in sys.argv:
    pattern_list = [
        'x/a/bc',        
        'y/abc',        
        'abcdef',
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

print sm.get_string(NormalizeF=False)

analyzer = core.Analyzer(sm, ForwardF=True)

for state in analyzer:
    if state.index == sm.init_state_index: assert state.input.move_input_position() == 0
    else:                                  assert state.input.move_input_position() == 1 
    print state.get_string(InputF=False, TransitionMapF=False)
