#! /usr/bin/env python
import sys
import generator_test

choice = generator_test.hwut_input("Pre Conditions: Pre-condtition vs. Backtracking", "SAME;")

pattern_list = [
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    'A/hello/',     
    'B/hello/',   
    'hello',
    '[A-Z][a-z]+'
]
pattern_action_pair_list = map(lambda re: (re, re.replace("\\t", "\\\\t").replace("\\n", "\\\\n")), 
                               pattern_list)

test_str = """AhelloBhellohellohelloworld"""
generator_test.do(pattern_action_pair_list, test_str, {}, choice, QuexBufferSize=60)    
