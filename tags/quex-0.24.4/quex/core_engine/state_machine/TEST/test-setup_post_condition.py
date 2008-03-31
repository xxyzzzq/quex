#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.state_machine.setup_post_context as setup_post_context
from   quex.core_engine.state_machine.TEST.test_state_machines import *
import quex.core_engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization as hopcroft

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Append Post Condition"
    sys.exit(0)

def test(sm, post_sm):    
    print "EXPRESSION = ", sm
    print "POST CONDITION = ", post_sm
    result = setup_post_context.do(sm, post_sm)
    print "APPENDED = ", result
    result = nfa_to_dfa.do(result)
    print "DFA = ", result
    result = hopcroft.do(result)
    print "HOPCROFT = ", result

print "-------------------------------------------------------------------------------"
tiny0 = StateMachine()
tiny0.add_transition(tiny0.init_state_index, ord('a'), AcceptanceF=True)

tiny1 = StateMachine()
tiny1.add_transition(tiny1.init_state_index, ord(';'), AcceptanceF=True)

test(tiny0, tiny1)    
    
print "-------------------------------------------------------------------------------"
sm = sm1 
post_sm = sm3.clone()

test(sm, post_sm)    
   

