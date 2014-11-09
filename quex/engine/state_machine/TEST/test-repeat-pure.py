#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.repeat as repeat 
from   quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Repetitions Kleene closure 0 or arbitrary repetitions"
    sys.exit(0)
    
print "-------------------------------------------------------------------------------"
print "##sm0", sm0
sm0r = repeat.kleene_closure(sm0) 
print "##result = ", sm0r

print "-------------------------------------------------------------------------------"
print "##sm1", sm1
sm1r = repeat.kleene_closure(sm1) 
print "##result = ", sm1r

print "-------------------------------------------------------------------------------"
print "##sm2", sm2
sm2r = repeat.kleene_closure(sm2) 
print "##result = ", sm2r
