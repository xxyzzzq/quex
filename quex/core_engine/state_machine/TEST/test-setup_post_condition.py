#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.core_engine.state_machine.setup_post_condition as setup_post_condition
from quex.core_engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Append Post Condition"
    sys.exit(0)

def test(sm, post_sm):    
    print "EXPRESSION = ", sm
    print "POST CONDITION = ", post_sm
    result = setup_post_condition.do(sm, post_sm)
    result.finalized_f = True    
    print "APPENDED = ", result
    result = result.get_DFA()
    print "DFA = ", result
    result = result.get_hopcroft_optimization()    
    print "HOPKINS = ", result

print "-------------------------------------------------------------------------------"
tiny0 = StateMachine()
tiny0.add_transition(tiny0.init_state_index, ord('a'), AcceptanceF=True)
tiny0.mark_state_origins()   

tiny1 = StateMachine()
tiny1.add_transition(tiny1.init_state_index, ord(';'), AcceptanceF=True)

test(tiny0, tiny1)    
    
print "-------------------------------------------------------------------------------"
sm = sm1 
sm.mark_state_origins()   
post_sm = sm3.clone()

test(sm, post_sm)    
   

