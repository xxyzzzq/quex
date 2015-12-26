#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.parallelize as parallelize 
from   quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "Tracing origin: Paralellization"
    sys.exit(0)

sm0.mark_state_origins()    
sm1.mark_state_origins()    
sm2.mark_state_origins()    

print "##sm0", sm0
print "##sm1", sm1
print "##sm2", sm2
sm = parallelize.do([sm0, sm1, sm2]) 

print "-------------------------------------------------------------------------------"
print "##result = ", sm

