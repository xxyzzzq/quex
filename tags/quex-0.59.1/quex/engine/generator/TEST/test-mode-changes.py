#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

choice = generator_test.hwut_input("CONTINUE: Mode Changes", "SAME;")

pattern_action_pair_list = [
        ('\\"',  "1: X ->2"),
        ('" "', "1: WHITESPACE CONTINUE"),
]
pattern_action_pair_list_2 = [
        ('\\"',  "2: X ->1"),
        ('" "', "2: WHITESPACE CONTINUE"),
]
test_str = "\" \""

generator_test.do(pattern_action_pair_list, test_str, {}, choice, 
                  SecondPatternActionPairList=pattern_action_pair_list_2)    
