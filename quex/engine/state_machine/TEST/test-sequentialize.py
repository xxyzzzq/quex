#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.sequentialize as sequentialize 
from quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Sequence"
    sys.exit(0)
   
empty_state_machine = StateMachine(7777)    
print "##sm0", sm0
print "##sm1", sm1
print "##sm2", sm2
sm = sequentialize.do([empty_state_machine, sm0, 
                       empty_state_machine, sm1, 
                       empty_state_machine, sm2,
                       empty_state_machine  ]) 

print "-------------------------------------------------------------------------------"
print "##result = ", sm
