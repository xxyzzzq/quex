#! /usr/bin/env python
import generator_test

choice = generator_test.hwut_input("CONTINUE: (special use case)", "SAME;")

pattern_action_pair_list = [
    ('x',    "X"),
    ('" "',  "WHITESPACE CONTINUE"),
]
test_str = "x x"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
