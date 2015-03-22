#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.parallelize as parallelize 
from   quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Paralell"
    sys.exit(0)


print "-------------------------------------------------------------------------------"
tsm0 = trivial_sm('a')
tsm1 = trivial_sm('b')
tsm2 = trivial_sm('c')
print "##tsm0:", tsm0
print "##tsm1:", tsm1
print "##tsm2:", tsm2

sm = parallelize.do([tsm0, tsm1, tsm2])
print "EXAMPLE 0:", sm

print "-------------------------------------------------------------------------------"
print "##sm0", sm0
print "##sm1", sm1
print "##sm2", sm2

print "-------------------------------------------------------------------------------"
sm = parallelize.do([sm0, sm1, sm2])
print "EXAMPLE A:", sm

print "-------------------------------------------------------------------------------"
empty_state_machine = StateMachine(7777)    
empty_state_machine.get_init_state().set_acceptance(True)
sm = parallelize.do([empty_state_machine, sm0, 
                     empty_state_machine, sm1, 
                     empty_state_machine, sm2, 
                     empty_state_machine]) 
print "EXAMPLE B:", sm
