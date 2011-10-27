#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.engine.state_machine.setup_pre_context as setup_pre_context 
from quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Setup Pre-Condition"
    sys.exit(0)

def test(sm, pre_sm):    
    print "EXPRESSION = ", sm
    print "PRE-CONDITION = ", pre_sm
    result = setup_pre_context.do(sm, pre_sm, False)
    #
    print "with pre-condition = ", result

print "-------------------------------------------------------------------------------"
tiny0 = StateMachine()
tiny0.add_transition(tiny0.init_state_index, ord('a'), AcceptanceF=True)
tiny1 = StateMachine()
tiny1.add_transition(tiny1.init_state_index, ord(';'), AcceptanceF=True)

test(tiny0, tiny1)    
    
print "-------------------------------------------------------------------------------"
test(sm1, sm3)    
   

