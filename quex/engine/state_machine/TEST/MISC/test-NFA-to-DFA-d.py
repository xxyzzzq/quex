#! /usr/bin/env python

# TEST: get_trigger_set_for_macro_state_transition(StateCombination0,
#                                                  StateCombination1)
#       from the module state_machine.construction.paralellize.
import sys
sys.path.append("../")
                        
from core import *
import paralellize 
import test_machine

from test_state_machines import *

# (*) UNIT TEST ________________________________________________________________
#
# -- test
result = paralellize.do([sm0, sm1, sm2])
print result

tmp = paralellize.map_combination_to_index.items()
tmp.sort(lambda a, b: cmp(a[1],b[1]))
for combination, index in tmp: 
    print index, combination

test_machine.do("abce", result)  # success of sm0
test_machine.do("ade", result)   # success of sm0
#
test_machine.do("aef", result)   # success of sm1
test_machine.do("bef", result)   # success of sm1
test_machine.do("gef", result)   # success of sm1
test_machine.do("abacfhixyef", result)   # success of sm1
test_machine.do("baabhiref", result)     # success of sm1
test_machine.do("gfbahef", result)      # success of sm1
# 
test_machine.do("gehX", result)      # success of sm2

