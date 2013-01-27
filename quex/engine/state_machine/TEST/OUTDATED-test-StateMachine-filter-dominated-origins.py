#! /usr/bin/env python
import sys
from random import random
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.state_machine.TEST.test_state_machines import *
from quex.engine.state_machine.index import *
import quex.engine.state_machine.parallelize as parallelize
import quex.engine.state_machine.repeat as repeat
import quex.engine.state_machine.algorithm.beautifier as beautifier

if "--hwut-info" in sys.argv:
    print "Ranking of state machines: Filter dominated origins"
    sys.exit(0)

#----------------------------------------------------------------------------------------    
# (*) setup the state machines    
sm0 = repeat.do(sm0)
sm0.mark_state_origins()
    
sm1.mark_state_origins()
sm2.mark_state_origins()
    
sm3 = repeat.do(sm3, 1)
sm3.mark_state_origins()

# -- paralellize the patterns    
sm = parallelize.do([sm0, sm1, sm2, sm3])
# -- create the optimized DFA for the patterns running in paralell
sm = beautifier.do(sm)    
    
#----------------------------------------------------------------------------------------    
# (*) create some priorities in between the patterns    
def add_priority(A, B):
    print "priority: %s > %s" % (repr(A.get_id()), repr(B.get_id()))    
    state_machine_ranking_db_register(A.get_id(), B.get_id())
    
add_priority(sm3, sm0)
add_priority(sm3, sm1)
add_priority(sm3, sm2)
add_priority(sm0, sm1)    
    
# register some more state relations for some of the states before
# to see if it confuses the algo. The additional states lie beyond
# 1000 so that they do not interfer with the original ones    
for i in range(10):
    X0 = long(random() * 10) + 1000    
    X1 = long(random() * 10) + 1000    
    try:    state_machine_ranking_db_register(X0, X1)
    except: pass
    try:    state_machine_ranking_db_register(A, X0)
    except: pass
    try:    state_machine_ranking_db_register(C, X1)
    except: pass
    try:    state_machine_ranking_db_register(E, X0)
    except: pass

print "---------------------------------------------------------------------"
print "(1) state machine with all its origin information"    
print
for state_idx, state in sm.states.items():
    acceptance_mark = " "
    if state.is_acceptance(): acceptance_mark = "*"
    print ("[%s]%s <~ " % (repr(state_idx), acceptance_mark)) + repr(state.origins().get_list()).replace("L", "")
print "---------------------------------------------------------------------"
print "(2) state machine with origins filtered"    
print
sm.filter_dominated_origins()
for state_idx, state in sm.states.items():
    acceptance_mark = " "
    if state.is_acceptance(): acceptance_mark = "*"
    print ("[%s]%s <~ " % (repr(state_idx), acceptance_mark)) + repr(state.origins().get_list()).replace("L", "")
print "---------------------------------------------------------------------"

