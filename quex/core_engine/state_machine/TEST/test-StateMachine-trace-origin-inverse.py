#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.parallelize as parallelize 
from quex.core_engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "Tracing origin: Inverse"
    sys.exit(0)

def invert_this(sm):
    print "-------------------------------------------------------------------------------"
    print "sm       = ", sm
    tmp = sm.get_inverse()
    print "inverse  = ", tmp 
    return tmp

sm0.mark_state_origins(); sm0.finalized_f = True    
# sm1.mark_state_origins(); sm1.finalized_f = True    
sm2.mark_state_origins(); sm2.finalized_f = True    
    
sm0 = invert_this(sm0)
# invert_this(sm1)
sm2 = invert_this(sm2)

sm = parallelize.do([sm0, sm2])  
sm.finalized_f = True    

print "-------------------------------------------------------------------------------"
print "## paralellized = ", sm
sm = sm.get_DFA()
sm = sm.get_hopcroft_optimization()    
print "## result = ",  sm
