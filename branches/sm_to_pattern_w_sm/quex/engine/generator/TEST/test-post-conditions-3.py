#! /usr/bin/env python
import generator_test

choice = generator_test.hwut_input("Post Conditions: Part 3", "SAME;")

pattern_action_pair_list = [
    ('x/[ \\t\\n]+',  "X / WHITESPACE"),
    ('y+/[ \\t\\n]+',  "y+ / WHITESPACE"),
    # whitespace
    ('[ \\t\\n]+',    "WHITESPACE")
]
test_str = "x   yy  y    "


generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
