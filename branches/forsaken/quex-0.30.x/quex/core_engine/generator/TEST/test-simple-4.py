#! /usr/bin/env python
import sys
import generator_test

if "--hwut-info" in sys.argv:
    print "Simple: The 'Nothing is Fine' / EOF Problem"
    sys.exit(0)

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('x*',      "X*"),
]
test_str = "aber-hallo"

try:
#    generator_test.do(pattern_action_pair_list, test_str, {}, choice, QuexBufferSize=5)    
    pass
except str, x:
    print dir(x)

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('<<EOF>>',  "EOF STOP"),
    ('x*',       "X*"),
]
test_str = "a"

generator_test.do(pattern_action_pair_list, test_str, {}, QuexBufferSize=5)    
