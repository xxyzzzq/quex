#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

if "--hwut-info" in sys.argv:
    print "CONTINUE: Mode Changes"
    print "CHOICES: PlainMemory, QuexBuffer;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Choice argument requested. Run --hwut-info"
    sys.exit(0)

choice = sys.argv[1]
if not (choice == "PlainMemory" or choice == "QuexBuffer"): 
    print "choice argument not acceptable"
    sys.exit(0)


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
