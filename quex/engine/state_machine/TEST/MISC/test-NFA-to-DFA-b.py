#! /usr/bin/env python
# TEST: get_trigger_set_for_macro_state_transition(StateCombination0,
#                                                  StateCombination1)
#       from the module state_machine.paralellize.
import sys
sys.path.append("../")
                        
from core import *
import paralellize 

from test_state_machines import *

# (*) UNIT TEST ________________________________________________________________
#
# -- setup
paralellize.state_machines  = [ sm0, sm1, sm2 ]
paralellize.state_machine_n = len(paralellize.state_machines)

# -- test
def consistency(combination):
    # check combination (does every state machine have the specified index)
    for i in range(len(combination)):
        assert paralellize.state_machines[i].states.has_key(combination[i]), \
               "state machine %i does not have a state (start or target) of %i" % \
               (i, combination[i])

def test(combination_0):

    followers = paralellize.get_follow_state_combinations(combination_0)

    print followers
    for combination in followers:
        consistency(combination)
        print "FROM: ", combination_0, "TO:", combination
        print paralellize.get_macro_state_transition(combination_0,
                                                     combination)

print "(*) test initial state combination"
test([sm0.init_state_index, sm1.init_state_index, sm2.init_state_index])

print "(*) test sm2 two before end"
test([-1, long(6), long(9) ])

print "(*) test sm2 just before end"
test([-1, -1, si2_3 ])

# test([ STATE_TERMINATION, si1_1, si2_2 ])
# print paralellize.get_follow_state_combinations(combination)
