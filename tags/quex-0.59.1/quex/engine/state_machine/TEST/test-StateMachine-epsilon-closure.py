#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.engine.state_machine.repeat as repeat 
from   quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "NFA: Epsilon closure (single state)"
    sys.exit(0)

test_sm0 = repeat.do(sm0, 1)

print "## state machine = ", test_sm0
print "## compute epsilon closures of all states:"

normal_epsilon_closures = []
for state_idx in test_sm0.states.keys():
    ec =  test_sm0.get_epsilon_closure(state_idx)
    ec.sort()
    if len(ec) != 1: print "state = ", state_idx, "epsilon-closure = ", ec
    else:            
        if ec[0] == state_idx: normal_epsilon_closures.append(state_idx)
        else:                  print "error: state idx", state_idx, " produces epsilon transition = ", ec

normal_epsilon_closures.sort()
print "## normal epsilon closures = ", normal_epsilon_closures
