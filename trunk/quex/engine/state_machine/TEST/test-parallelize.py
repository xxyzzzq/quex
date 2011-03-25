#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.state_machine.core import *
import quex.engine.state_machine.parallelize as parallelize 
from   quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Paralell"
    sys.exit(0)

print "##sm0", sm0
print "##sm1", sm1
print "##sm2", sm2

print "-------------------------------------------------------------------------------"
sm = parallelize.do([sm0, sm1, sm2])
print "EXAMPLE A:", sm

print "-------------------------------------------------------------------------------"
empty_state_machine = StateMachine(7777)    
sm = parallelize.do([empty_state_machine, sm0, 
                     empty_state_machine, sm1, 
                     empty_state_machine, sm2, 
                     empty_state_machine]) 
print "EXAMPLE B:", sm
