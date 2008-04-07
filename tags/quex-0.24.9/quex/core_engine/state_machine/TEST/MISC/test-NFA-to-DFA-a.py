#! /usr/bin/env python
# PURPOSE:
#   Tests the function "get_follow_state_combinations(state_combination)"
#   from the module state_machine.paralellize.
#
################################################################################

import sys
sys.path.append("../")

from core import *
import paralellize 

from test_state_machines import *

# (*) UNIT TEST ________________________________________________________________
#
paralellize.state_machines  = [ sm0, sm1, sm2 ]
paralellize.state_machine_n = len(paralellize.state_machines)

combination = [sm0.init_state_index,
               sm1.init_state_index,
               sm2.init_state_index]
print repr(paralellize.get_follow_state_combinations(combination)).replace("L", "")
print

combination = [si0_1, si1_1, si2_2 ]
print repr(paralellize.get_follow_state_combinations(combination)).replace("L", "")
print

combination = [ STATE_TERMINATION, si1_2, si2_2 ]
print repr(paralellize.get_follow_state_combinations(combination)).replace("L", "")
print


