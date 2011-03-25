#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.core_engine.state_machine.repeat as repeat
from   quex.core_engine.state_machine.core import *
from   quex.core_engine.state_machine.TEST.test_state_machines import *
import quex.core_engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization as hopcroft

if "--hwut-info" in sys.argv:
    print "DFA: Hopcroft optimization (minimize state set)"
    print "CHOICES: NEW, ADAPT;"
    print "SAME;"
    sys.exit(0)

if "NEW" in sys.argv:     CreateNewStateMachineF=True
elif "ADAPT" in sys.argv: CreateNewStateMachineF=False
else:
    print "Require command line arguments: '--hwut-info', 'NEW', or 'ADAPT'"
    sys.exit(-1)

print "_______________________________________________________________________________"
print "Example A:"
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm = repeat.do(sm, 1)
dfa = nfa_to_dfa.do(sm)
print hopcroft.do(dfa, CreateNewStateMachineF=CreateNewStateMachineF)

print "_______________________________________________________________________________"
print "Example B:"
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm = repeat.do(sm)
dfa = nfa_to_dfa.do(sm)
print hopcroft.do(dfa, CreateNewStateMachineF=CreateNewStateMachineF)

print "_______________________________________________________________________________"
print "Example C:"
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm = repeat.do(sm, 0, 1)
dfa = nfa_to_dfa.do(sm)
# print dfa.get_string(NormalizeF=False)
print hopcroft.do(dfa, CreateNewStateMachineF=CreateNewStateMachineF)

print "_______________________________________________________________________________"
print "Example D:"
sm = StateMachine()
n0 = sm.init_state_index     
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
sm = repeat.do(sm, 3, 5)
dfa = nfa_to_dfa.do(sm)
print hopcroft.do(dfa, CreateNewStateMachineF=CreateNewStateMachineF)

print "_______________________________________________________________________________"
print "Example E:"
# (*) create a simple state machine:  
#                                    ,-- 'b' --.
#                                   /          |
#                     ,-- 'b' -->((2)) <------'
#                    /           /  '\ 
#    (0)-- 'a' -->((1))        'c'   'b'
#                    \           \,  /
#                     '-- 'c' -->((3))<-------.
#                                   \         |
#                                    '-- 'c'--'
#
#    ((1)), ((2)), and ((3))  are the acceptance states.
#
sm = StateMachine()
n0 = sm.init_state_index
n1 = sm.add_transition(n0, ord('a'), AcceptanceF=True)
n2 = sm.add_transition(n1, ord('b'), AcceptanceF=True)
n3 = sm.add_transition(n1, ord('c'), AcceptanceF=True)
sm.add_transition(n2, ord('b'), n2)
sm.add_transition(n3, ord('c'), n3)
sm.add_transition(n2, ord('c'), n3)
sm.add_transition(n3, ord('b'), n2)

# (*) minimize the number of states using hopcroft optimization
optimal_sm = hopcroft.do(sm, CreateNewStateMachineF=CreateNewStateMachineF)
print optimal_sm

print "_______________________________________________________________________________"
print "Example F:"
optimal_sm = hopcroft.do(sm3, CreateNewStateMachineF=CreateNewStateMachineF) # .get_string(NormalizeF=True)
print optimal_sm
