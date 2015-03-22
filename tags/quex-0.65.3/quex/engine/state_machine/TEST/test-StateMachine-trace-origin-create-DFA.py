#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core import *
from quex.engine.state_machine.state.core import *
from quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.algorithm.nfa_to_dfa as nfa_to_dfa

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
n9 = sm.add_epsilon_transition(n8)
set_cmd_list(sm, n9, (55, 0, True))
#
sm.add_epsilon_transition(n2, n9)
sm.add_epsilon_transition(n8, n3)

#set_cmd_list(sm, n0, (66, 0, False), (77, 0, False), (88, 0, False))
#set_cmd_list(sm, n4, (77, 1, False))
#set_cmd_list(sm, n6, (88, 22, True))
sm.states[n6].set_input_position_store_f(True)
sm.states[n6].mark_acceptance_id(88)


# (*) create the DFA from the specified NFA
# print sm.get_string(NormalizeF=False)
dfa = nfa_to_dfa.do(sm)
print dfa

