#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

if "--hwut-info" in sys.argv:
    print "Pre- and Post- Conditions: Simple"
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
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # other characters
    ('[a-wz]+',                            "OTHER+"),
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    ('"hello"[ \\t]+/"x"+/[ \\t]+"world"', "HELLO / X+ / WORLD"),
    # 
    ('"x"+/[ \\t]+"world"',                "X+ / WORLD"),
    # repetition of 'x' (one or more) **preceded** by 'good' + whitespace
    ('"hello"[ \\t]+/"x"+/',               "HELLO WSPC. / X+ /"),
    # normal repetition (one or more) of 'x'
    ('"x"+',                               "X+"),
    # whitespace
    ('[ \\t\\n]+',                         "WHITESPACE")
]
test_str = "x  hello xxxbonjour hello xx  world xx world hello xxx x x"


generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
