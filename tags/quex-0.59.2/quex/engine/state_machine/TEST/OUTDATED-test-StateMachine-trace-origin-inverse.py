#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.state_machine.core import *
import quex.engine.state_machine.parallelize as parallelize 
from quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.hopcroft_minimization as hopcroft

if "--hwut-info" in sys.argv:
    print "Tracing origin: Inverse"
    sys.exit(0)

def invert_this(sm):
    print "-------------------------------------------------------------------------------"
    print "sm       = ", sm
    tmp = sm.get_inverse()
    print "inverse  = ", tmp 
    return tmp

sm0.mark_state_origins() 
# sm1.mark_state_origins()
sm2.mark_state_origins()
    
sm0 = invert_this(sm0)
# invert_this(sm1)
sm2 = invert_this(sm2)

sm = parallelize.do([sm0, sm2])  

print "-------------------------------------------------------------------------------"
print "## paralellized = ", sm
sm = nfa_to_dfa.do(sm)
sm = hopcroft.do(sm)
print "## result = ",  sm
