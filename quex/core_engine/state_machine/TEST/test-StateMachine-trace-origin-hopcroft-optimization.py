#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.hopcroft_minimization as hopcroft

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

sm.states[n0].add_origin(0L, 0L)
sm.states[n0].add_origin(1L, 0L)
sm.states[n0].add_origin(2L, 0L)
sm.states[n1].add_origin(0L, 66L)
sm.states[n1].add_origin(1L, 66L)
sm.states[n1].add_origin(2L, 66L)
sm.states[n2].add_origin(0L, 77L)
sm.states[n2].add_origin(0L, 77L)
sm.states[n2].add_origin(2L, 77L)
sm.states[n2].add_origin(1L, 77L)
sm.states[n3].add_origin(0L, 88L)
sm.states[n3].add_origin(1L, 88L)
sm.states[n3].add_origin(2L, 88L)

print sm
# (*) minimize the number of states using hopcroft optimization
optimal_sm = hopcroft.do(sm)
print optimal_sm

