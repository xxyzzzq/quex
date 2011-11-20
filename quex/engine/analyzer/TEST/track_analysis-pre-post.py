#! /usr/bin/env python
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine  as regex
from   quex.engine.generator.base            import get_combined_state_machine
from   quex.engine.analyzer.core             import E_InputActions
import quex.engine.analyzer.core             as core
import help

if "--hwut-info" in sys.argv:
    print "Track Analyzis: With Pre- and Post-Contexts;"
    print "CHOICES: 1, 2, 3, 4, 5, 6, 7, 9;"
    sys.exit()

if   "1" in sys.argv:
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
        'y/abc/',        
        'abcdef',
    ]
elif "5" in sys.argv:
    # Check that positions are stored even for dominated pre-contexts.
    # Pattern "a" dominates "x/a/aa/" when an 'a' arrives. But, at the
    # position of "c" in "(aaa|bb)cd" the pattern "x/a/aa" must win
    # and the right positioning must be applied.
    pattern_list = [
        "aa?",
        "x/a/aa",
        "b",
        "(aaa|bb)cd",
    ]
elif "6" in sys.argv:
    # A pre-context dominates another one, but at some point later the
    # positioning of the 'dominated' must be applied. This is similar
    # to the previous case, but it is not concerned with the 'cut' of
    # the unconditional pattern "aa?" as above.
    pattern_list = [
        "x/aa?/",    # (1) dominating (mentioned first)
        "y/a/aaa",   # (2) dominated (wins by length)
        "aaaab",
    ]
elif "7" in sys.argv:
    # Non-uniform traces with multiple pre-contexts
    pattern_list = [
        '0/a+/',
        '1/b/',
        '2/(a+|bc+)/d+ef',
        '3/(a+|bc+)d+/ef',
        '4/(a+|bc+)d+e/f',
    ]
elif "9" in sys.argv:
    # Non-uniform traces with multiple pre-contexts
    pattern_list = [
        'x/a/',
        'x/b/',
        'x/(a|bb?c?)de/',
        'x/(a|bb?c?)d/e',
    ]
else:
    assert False


state_machine_list = map(lambda x: regex.do(x, {}).sm, pattern_list)

sm  = get_combined_state_machine(state_machine_list, False) # May be 'True' later.
sm  = sm.normalized_clone()

# For DEBUG purposes: specify 'DRAW' on command line
help.if_DRAW_in_sys_argv(sm)
help.test(sm)

