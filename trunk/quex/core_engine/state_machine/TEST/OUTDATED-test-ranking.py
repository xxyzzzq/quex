#! /usr/bin/env python
import sys
from random import random
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.index import *

if "--hwut-info" in sys.argv:
    print "Ranking of state machines: Pattern priorization"
    sys.exit(0)

A = 66L
B = 77L
C = 88L
D = 99L
E = 11L
F = 22L
state_machine_ranking_db_register(A, B)
state_machine_ranking_db_register(B, C)
state_machine_ranking_db_register(C, D)
state_machine_ranking_db_register(D, E)
state_machine_ranking_db_register(E, F)
# register some more state relations for some of the states before
# to see if it confuses the algo. The additional states lie beyond
# 1000 so that they do not interfer with the original ones    
for i in range(100):
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

print "(*) data base ranking chain A > B > C > D > E > F, unrelated = 10"    
print "    NOTE: False means 'no assumption' according to ranking db."
print "    A > F ?   ", state_machine_ranking_db_is_superior(A, F)    
print "    A < F ?   ", state_machine_ranking_db_is_superior(F, A)    
print "    A < 10 ?  ", state_machine_ranking_db_is_superior(A, 10)    
print "    10 < A ?  ", state_machine_ranking_db_is_superior(10, A)    



