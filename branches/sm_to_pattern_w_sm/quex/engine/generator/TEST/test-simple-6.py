#! /usr/bin/env python
import generator_test
import sys

if "--hwut-info" in sys.argv:
    print "Simple: Reload Init State;"
    print "CHOICES: ANSI-C, Cpp-Template, Cpp-Path;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["ANSI-C", "Cpp-Template", "Cpp-Path"]): 
    print "Language argument not acceptable, use --hwut-info"
    sys.exit(0)

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('AZ',     "A_Z"),
    ('A*X', "A_STAR_X"),
    ('A*Y', "A_STAR_Y"),
]
test_str = "AZXAXAAXYAYAAY"

generator_test.do(pattern_action_pair_list, test_str, {}, sys.argv[1], QuexBufferSize=5)    
