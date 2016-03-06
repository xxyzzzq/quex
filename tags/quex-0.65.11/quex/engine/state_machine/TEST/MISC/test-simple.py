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

print sm0
test_machine.do("abce", sm0)  # success of sm0
test_machine.do("abcf", sm0)  # fail of sm0
test_machine.do("ade", sm0)  # fail of sm0
#
print sm2
test_machine.do("gehgehgehgehX", sm2)      # success of sm2

