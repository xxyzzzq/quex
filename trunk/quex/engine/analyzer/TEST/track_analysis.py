#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
from   quex.engine.analyzer.core             import InputActions
import quex.engine.analyzer.core             as core
import help_drawing

if "--hwut-info" in sys.argv:
    print "Track Analyzis: Without Pre- and Post-Contexts;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9;"
    sys.exit()

if "0" in sys.argv:
    pattern_list = [
        'a',        
        'ab',     
    ]
   #    ┌────┐  a   ┌────┐  b   ┌────┐
   #    │ 26 │ ───▶ │ 27 │ ───▶ │ 28 │
   #    └────┘      └────┘      └────┘
   #____________________________________________________________________

elif "1" in sys.argv:
    pattern_list = [
        'a',        
        'abc',     
    ]
   #    ┌────┐  a   ┌────┐  b   ┌────┐  c   ┌────┐
   #    │ 37 │ ───▶ │ 38 │ ───▶ │ 39 │ ───▶ │ 40 │
   #    └────┘      └────┘      └────┘      └────┘
   #____________________________________________________________________

elif "2" in sys.argv:
    pattern_list = [
        'a',        
        'b',     
        '[ab]c'
    ]
   #    ┌────┐  a   ┌────┐  c   ┌────┐
   #    │ 35 │ ───▶ │ 36 │ ───▶ │ 38 │
   #    └────┘      └────┘      └────┘
   #      │                       ▲
   #      │ b                     │
   #      ▼                       │
   #    ┌────┐  c                 │
   #    │ 37 │ ───────────────────┘
   #    └────┘
   #____________________________________________________________________

elif "3" in sys.argv:
    pattern_list = [
        'a',        
        'b',     
        '[ab]cd'
    ]
   #    ┌────┐  a   ┌────┐  c   ┌────┐  d   ┌────┐
   #    │ 45 │ ───▶ │ 46 │ ───▶ │ 48 │ ───▶ │ 49 │
   #    └────┘      └────┘      └────┘      └────┘
   #      │                       ▲
   #      │ b                     │
   #      ▼                       │
   #    ┌────┐  c                 │
   #    │ 47 │ ───────────────────┘
   #    └────┘
   #____________________________________________________________________

elif "4" in sys.argv:
    pattern_list = [
        'aa?',        
        'aa?cd'
    ]
   #                       c
   #                  ┌───────────────────────┐
   #                  │                       ▼
   #    ┌────┐  a   ┌────┐  a   ┌────┐  c   ┌────┐  d   ┌────┐
   #    │ 56 │ ───▶ │ 57 │ ───▶ │ 59 │ ───▶ │ 58 │ ───▶ │ 60 │
   #    └────┘      └────┘      └────┘      └────┘      └────┘
   #____________________________________________________________________

elif "5" in sys.argv:
    pattern_list = [
        '[ab]',        
        '((aa?)|b)cd'
    ]
   #                       c
   #                  ┌───────────────────────┐
   #                  │                       ▼
   #    ┌────┐  a   ┌────┐  a   ┌────┐  c   ┌────┐  d   ┌────┐
   #    │ 68 │ ───▶ │ 69 │ ───▶ │ 73 │ ───▶ │ 71 │ ───▶ │ 72 │
   #    └────┘      └────┘      └────┘      └────┘      └────┘
   #      │                                   ▲
   #      │ b                                 │
   #      ▼                                   │
   #    ┌────┐  c                             │
   #    │ 70 │ ───────────────────────────────┘
   #    └────┘
   #____________________________________________________________________

elif "6" in sys.argv:
    pattern_list = [
        '[ab]',        
        '((ab)|b)cd',
    ]
   #    ┌────┐  a   ┌────┐  b   ┌────┐  c   ┌────┐  d   ┌────┐
   #    │ 68 │ ───▶ │ 69 │ ───▶ │ 73 │ ───▶ │ 71 │ ───▶ │ 72 │
   #    └────┘      └────┘      └────┘      └────┘      └────┘
   #      │                                   ▲
   #      │ b                                 │
   #      ▼                                   │
   #    ┌────┐  c                             │
   #    │ 70 │ ───────────────────────────────┘
   #    └────┘
   #____________________________________________________________________

elif "7" in sys.argv:
    pattern_list = [
        'a+',        
        'b+c',        
        '(a+|(b+c))de',
    ]
   #                             b
   #                           ┌───┐
   #                           ▼   │
   #          ┌───────┐  b   ┌───────┐  c   ┌─────┐  d   ┌─────┐  e   ┌─────┐
   #      ┌── │  131  │ ───▶ │  133  │ ───▶ │ 134 │ ───▶ │ 135 │ ───▶ │ 136 │
   #      │   └───────┘      └───────┘      └─────┘      └─────┘      └─────┘
   #      │       a                                        ▲
   #      │ a   ┌───┐                                      │
   #      │     ▼   │                                      │
   #      │   ┌───────┐  d                                 │
   #      └─▶ │  132  │ ───────────────────────────────────┘
   #          └───────┘
   #____________________________________________________________________

elif "8" in sys.argv:
    pattern_list = [
        'a+',        
        'b',        
        '(a+|(bc+))de',
    ]
   #                                          c
   #                                        ┌───┐
   #                                        ▼   │
   #          ┌───────┐  b   ┌─────┐  c   ┌───────┐  d   ┌─────┐  e   ┌─────┐
   #      ┌── │  112  │ ───▶ │ 114 │ ───▶ │  115  │ ───▶ │ 116 │ ───▶ │ 117 │
   #      │   └───────┘      └─────┘      └───────┘      └─────┘      └─────┘
   #      │       a                                        ▲
   #      │ a   ┌───┐                                      │
   #      │     ▼   │                                      │
   #      │   ┌───────┐  d                                 │
   #      └─▶ │  113  │ ───────────────────────────────────┘
   #          └───────┘
   #____________________________________________________________________

elif "9" in sys.argv:
    pattern_list = [
        'if',        
        '[a-z]+',
    ]
   #           ['a', 'h'], ['j', 'z']
   #      ┌────────────────────────────────────────────┐
   #      │                                            ▼
   #    ┌────┐      ┌────┐      ┌────┐               ┌────┐   ['a', 'z']
   #    │    │      │    │      │    │               │    │ ─────────────┐
   #    │ 39 │  i   │ 41 │  f   │ 42 │  ['a', 'z']   │ 40 │              │
   #    │    │ ───▶ │    │ ───▶ │    │ ────────────▶ │    │ ◀────────────┘
   #    └────┘      └────┘      └────┘               └────┘
   #                  │    ['a', 'e'], ['g', 'z']      ▲
   #                  └────────────────────────────────┘
   #____________________________________________________________________

elif "Nonsense" in sys.argv:
    pattern_list = [
        'ade',
        'abc',        
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}), pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.

# For DEBUG purposes: specify 'DRAW' on command line
help_drawing.if_DRAW_in_sys_argv(sm)

print sm.get_string(NormalizeF=False)

analyzer = core.Analyzer(sm)

for state in analyzer:
    if state.index == sm.init_state_index: 
        assert state.input == InputActions.DEREF
    else:
        assert state.input == InputActions.INCREMENT_THEN_DEREF

    print state.get_string(InputF=False, TransitionMapF=False)
