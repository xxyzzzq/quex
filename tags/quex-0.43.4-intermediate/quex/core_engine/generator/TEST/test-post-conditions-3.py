#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

if "--hwut-info" in sys.argv:
    print "Post Conditions: Part 3"
    print "CHOICES: ANSI-C-PlainMemory, ANSI-C, Cpp, Cpp_StrangeStream;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2:
    print "Choice argument requested. Run --hwut-info"
    sys.exit(0)

choice = sys.argv[1]
if not (choice in ["ANSI-C-PlainMemory", "ANSI-C", "Cpp", "Cpp_StrangeStream"]): 
    print "choice argument not acceptable"
    sys.exit(0)

pattern_action_pair_list = [
    ('x/[ \\t\\n]+',  "X / WHITESPACE"),
    ('y+/[ \\t\\n]+',  "y+ / WHITESPACE"),
    # whitespace
    ('[ \\t\\n]+',    "WHITESPACE")
]
test_str = "x   yy  y    "


generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
