#! /usr/bin/env python
import generator_test

import sys

if "--hwut-info" in sys.argv:
    print "Mode Changes;"
    print "CHOICES: ANSI-C, Cpp, ANSI-C-CG;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C", "Cpp", "ANSI-C-CG"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

choice = sys.argv[1]


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
