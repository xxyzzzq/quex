#! /usr/bin/env python
import sys
import generator_test

if "--hwut-info" in sys.argv:
    print "Simple: Special Case '.' (drop out on valid target state)"
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
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('.',      "."),
]
test_str = "aber-hallo"

generator_test.do(pattern_action_pair_list, test_str, {}, choice, QuexBufferSize=5)    
