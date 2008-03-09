#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.nfa_to_dfa as nfa_to_dfa

if "--hwut-info" in sys.argv:
    print "Tracing origin: NFA to DFA (subset construction)"
    sys.exit(0)
    
# (*) create a simple state machine:  
#                                            ,--<------------ eps ------------------.
#                                           /                                        \
#                                          |   ,- eps -->(4)-- 'b' -->(5)-- eps -.   |
#                                           \ /                                   \ /
#    (0)-- 'a' -->(1)-- eps -->(2)-- eps -->(3)                                   (8)-- eps -->((9))
#                                \            \                                   /            /
#                                 \            '- eps -->(6)-- 'c' -->(7)-- eps -'            /
#                                  \                                                         /
#                                   '----------------------- eps ----------->---------------'
#
#    ((9)) is the acceptance state.
#
sm = StateMachine()
n0 = sm.init_state_index
n1 = sm.add_transition(n0, ord('a'))
n2 = sm.add_epsilon_transition(n1)
n3 = sm.add_epsilon_transition(n2)
# 
n4 = sm.add_epsilon_transition(n3)
n5 = sm.add_transition(n4, ord('b'))
#
n6 = sm.add_epsilon_transition(n3)
n7 = sm.add_transition(n6, ord('c'))
n8 = sm.add_epsilon_transition(n7)
#
sm.add_epsilon_transition(n5, n8)
#
n9 = sm.add_epsilon_transition(n8, RaiseAcceptanceF=True)
#
sm.add_epsilon_transition(n2, n9)
sm.add_epsilon_transition(n8, n3)

sm.states[n0].add_origin(66L, 0L)    
sm.states[n0].add_origin(77L, 0L)    
sm.states[n0].add_origin(88L, 0L)    
sm.states[n4].add_origin(77L, 1L)    
sm.states[n6].add_origin(88L, 22L, True)    


# (*) create the DFA from the specified NFA
dfa = nfa_to_dfa.do(sm)
print dfa

