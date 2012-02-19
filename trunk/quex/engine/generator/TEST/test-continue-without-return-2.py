#! /usr/bin/env python
import generator_test
import sys

if "--hwut-info" in sys.argv:
    print "Simple: Reload Init State;"
    print "CHOICES: ANSI-C, Cpp, ANSI-C-CG;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C", "Cpp", "ANSI-C-CG"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

choice = sys.argv[1]


pattern_action_pair_list = [
    ('x',    "X"),
    ('" "',  "WHITESPACE CONTINUE"),
]
test_str = "x x"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
