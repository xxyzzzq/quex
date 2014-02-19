#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.generator.code.base              import SourceRef_VOID
import quex.engine.state_machine.setup_post_context as setup_post_context
from   quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.algorithm.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.algorithm.hopcroft_minimization as hopcroft

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Append Post Condition"
    sys.exit(0)

def test(sm, post_sm):    
    print "EXPRESSION = ", sm
    print "POST CONDITION = ", post_sm
    return_sm = setup_post_context.do(sm, post_sm, False, SourceRef_VOID)
    print "APPENDED = ", sm
    sm = nfa_to_dfa.do(sm)
    print "DFA = ", sm
    sm = hopcroft.do(sm)
    print "HOPCROFT = ", sm

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
   

