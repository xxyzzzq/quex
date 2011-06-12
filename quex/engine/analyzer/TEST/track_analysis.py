#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
import quex.engine.analyzer.core             as core

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Without Pre- and Post-Contexts;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9;"
    sys.exit()

if "0" in sys.argv:
    """
    ╔════╗  a   ╔════╗  b   ╔════╗
    ║ 26 ║ ───▶ ║ 27 ║ ───▶ ║ 28 ║
    ╚════╝      ╚════╝      ╚════╝
    """
    pattern_list = [
        'a',        
        'ab',     
    ]
elif "1" in sys.argv:
    pattern_list = [
        'a',        
        'abc',     
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
elif "7" in sys.argv:
    pattern_list = [
        'a+',        
        'b+c',        
        '(a+|(b+c))de',
    ]
elif "8" in sys.argv:
    pattern_list = [
        'a+',        
        'b',        
        '(a+|(bc+))de',
    ]
elif "9" in sys.argv:
    pattern_list = [
        'if',        
        '[a-z]+',
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

if False:
    fh = open("tmp.dot", "wb")
    fh.write( sm.get_graphviz_string() )
    fh.close()
    os.system("graph-easy --input=tmp.dot --as boxart")

print sm.get_string(NormalizeF=False)

analyzer = core.Analyzer(sm, ForwardF=True)

for state in analyzer:
    if state.index == sm.init_state_index: assert state.input.move_input_position() == 0
    else:                                  assert state.input.move_input_position() == 1 
    print state.get_string(InputF=False, TransitionMapF=False)
