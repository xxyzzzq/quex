#! /usr/bin/env python
import generator_test

choice = generator_test.hwut_input("Pre- and Post- Conditions: Simple", "SAME;")

pattern_action_pair_list = [
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # other characters
    ('[a-wz]+',                            "OTHER+"),
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    ('"hello"[ \\t]+/"x"+/[ \\t]+"world"', "HELLO / X+ / WORLD"),
    # 
    ('"x"+/[ \\t]+"world"',                "X+ / WORLD"),
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    ('"hello"[ \\t]+/"x"+/',               "HELLO WSPC. / X+ /"),
    # normal repetition (one or more) of 'x'
    ('"x"+',                               "X+"),
    # whitespace
    ('[ \\t\\n]+',                         "WHITESPACE")
]
test_str = "x  hello xxxbonjour hello xx  world xx world hello xxx x x"


generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
