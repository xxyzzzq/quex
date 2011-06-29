#! /usr/bin/env python
import sys
import generator_test
from   generator_test import action, hwut_input

choice = hwut_input("Simple: Begin of Line (BOL), End of Line (EOL)", "SAME;")

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('^[A-Z]+":"',     "BOL-LABEL"),
    ('[A-Z]+":"',      "LABEL"),
    ('"PRINT"',        "KEYWORD"),
    ('[A-Z]+',         "IDENTIFIER"),
    ('[A-Z]+$',        "EOL-IDENTIFIER"),
    ('[ \\t]+',        "WHITESPACE"),
    ('\\n',            "NEWNLINE"),
]
test_str = \
"""HERE: THERE:
THIS  THAT
HERE: THERE:
THIS  THAT"""

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
