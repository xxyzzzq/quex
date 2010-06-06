#! /usr/bin/env python
import sys
import generator_test

choice = generator_test.hwut_input("Pre Conditions: Part 1", "SAME;")

pattern_action_pair_list = [
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    ('[ \\t]+/"x"+/',        "WHITESPACE / X+ /"),
    ('[ \\t]+/"xz"/',        "WHITESPACE / XZ /"),
    # normal repetition (one or more) of 'x'
    ('"x"+',                 "X+"),
    # whitespace
    ('[ \\t\\n]+',           "WHITESPACE")
]
test_str = "x  xxxxx xxx x"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
