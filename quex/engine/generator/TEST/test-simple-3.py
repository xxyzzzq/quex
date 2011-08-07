#! /usr/bin/env python
import generator_test

choice = generator_test.hwut_input("Simple: Special Case '.' (drop out on valid target state)", "SAME;")

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('.',      "."),
]
test_str = "aber-hallo"

generator_test.do(pattern_action_pair_list, test_str, {}, choice, QuexBufferSize=5)    
