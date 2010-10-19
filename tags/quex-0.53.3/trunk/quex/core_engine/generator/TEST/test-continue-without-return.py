#! /usr/bin/env python
import sys
import  generator_test 

choice = generator_test.hwut_input("CONTINUE: Reentry analysis without return from function", 
                                   "SAME;")

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('[A-Z]+":"',      "LABEL"),
    ('"PRINT"',        "KEYWORD CONTINUE"),
    ('[A-Z]+',         "IDENTIFIER CONTINUE"),
    ('[ \\t]+',        "WHITESPACE CONTINUE"),
]
test_str = "ABERHALLO: GUGU PRINT PRINT: PRINTERLEIN"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
