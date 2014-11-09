#! /usr/bin/env python

# TEST: get_trigger_set_for_macro_state_transition(StateCombination0,
#                                                  StateCombination1)
#       from the module state_machine.construction.paralellize.
import sys
sys.path.append("../")
                        
from core import *
import paralellize 

from test_state_machines import *

# (*) UNIT TEST ________________________________________________________________
#
# -- setup
paralellize.state_machines       = [ sm0, sm1, sm2 ]
paralellize.state_machine_n      = len(paralellize.state_machines)
paralellize.result_state_machine = StateMachine()

# -- test
def test(combination_0):
    paralellize.append_macro_state_transitions(combination_0)
    tmp = paralellize.map_combination_to_index.items()
    tmp.sort(lambda a, b: cmp(a[1],b[1]))
    for combination, index in tmp: 
        print index, combination
    print paralellize.result_state_machine


# test([sm0.init_state_index, sm1.init_state_index, sm2.init_state_index])

test([STATE_TERMINATION, STATE_TERMINATION, long(10) ])
# print paralellize.get_follow_state_combinations(combination)

#test([ STATE_FAIL, si1_1, si2_2 ])
# print paralellize.get_follow_state_combinations(combination)
