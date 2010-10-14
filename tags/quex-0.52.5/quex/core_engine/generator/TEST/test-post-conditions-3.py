#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

choice = generator_test.hwut_input("Post Conditions: Part 3", "SAME;")

pattern_action_pair_list = [
    ('x/[ \\t\\n]+',  "X / WHITESPACE"),
    ('y+/[ \\t\\n]+',  "y+ / WHITESPACE"),
    # whitespace
    ('[ \\t\\n]+',    "WHITESPACE")
]
test_str = "x   yy  y    "


generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
