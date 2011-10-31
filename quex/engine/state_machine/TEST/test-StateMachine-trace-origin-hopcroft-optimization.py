#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.state_machine.core import *
from   quex.engine.state_machine.state_core_info import *
import quex.engine.state_machine.algorithm.hopcroft_minimization as hopcroft

if "--hwut-info" in sys.argv:
    print "Tracing origin: Hopcroft optimization (minimize state set)"
    sys.exit(0)

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
print sm

def set_origins(StateIndex, TheList):
    global sm
    sm.states[StateIndex].origins().set(
        [ StateCoreInfo(long(sm_id), long(state_index), acceptance_f) for sm_id, state_index, acceptance_f in TheList ]
    )

set_origins(n0, [(0, 0,  False), (1, 0,  False), (2, 0,  False)])
set_origins(n1, [(0, 66, True), (1, 66, True), (2, 66, True)])
set_origins(n2, [(0, 77, True), (0, 77, True), (2, 77, True), (1, 77, True)])
set_origins(n3, [(0, 88, True), (1, 88, True), (2, 88, True)])

print sm
# (*) minimize the number of states using hopcroft optimization
optimal_sm = hopcroft.do(sm)
print optimal_sm

