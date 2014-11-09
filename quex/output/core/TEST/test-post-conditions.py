#! /usr/bin/env python
import sys
sys.path.append("../../../../")
import generator_test

import sys

if "--hwut-info" in sys.argv:
    print "Post Conditions: Part I;"
    print "CHOICES: ANSI-C, Cpp, ANSI-C-CG;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C", "Cpp", "ANSI-C-CG"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

choice = sys.argv[1]

pattern_action_pair_list = [
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # normal repetition (one or more) of 'x'
    ('"x"+',           "X+"),
    # repetition of 'x' (one or more) **followed** by 'anonymous' whitespace
    ('"x"+/([ \\t]+)', "X+ / WS"),
    # whitespace
    ('[ \\t\\n]+',     "WHITESPACE")
]
test_str = "x   xxxxx xxx x"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
