#! /usr/bin/env python
import generator_test 

choice = generator_test.hwut_input("Simple: Tiny Expressions", "SAME;")

pattern_action_pair_list = [
    # pre-contexted expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('[A-Z]+":"',      "LABEL"),
    ('"PRINT"',        "KEYWORD"),
    ('[A-Z]+',         "IDENTIFIER"),
    ('[ \\t]+',        "WHITESPACE"),
]
test_str = "ABERHALLO: GUGU PRINT PRINT: PRINTERLEIN"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
