#! /usr/bin/env python
import generator_test

choice = generator_test.hwut_input("Pseudo Ambgiguous Post Condition: Part I", "SAME;")

pattern_list = [
    # -- pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    #    otherwise, the un-conditional expressions gain precedence and the un-conditional
    #    pattern is never matched.
    #
    # -- post-conditioned patterns do not need to appear before the same non-postconditioned
    #    patterns, since they are always longer.
    #
    # normal repetition (one or more) of 'x'
    'x+/x',
    # other characters
    '[a-z]+',
    # whitespace
    '[ \\t\\n]+'
]
pattern_action_pair_list = map(lambda x: [x, x.replace("\\", "\\\\")], pattern_list)

test_str = "xxx x xx x"


generator_test.do(pattern_action_pair_list, test_str, {}, choice, QuexBufferSize=10)    

