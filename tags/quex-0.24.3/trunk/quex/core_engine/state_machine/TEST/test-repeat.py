#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.repeat as repeat 
from quex.core_engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Repetition with min and max repetition numbers"
    sys.exit(0)
    
print "-------------------------------------------------------------------------------"
print "##sm0", sm3
print "## repeat.do(sm3) "
sm3r = repeat.do(sm3) 
print "##result = ", sm3r

print "-------------------------------------------------------------------------------"
print "##sm0", sm3
print "## repeat.do(sm3, 2) "
sm3r = repeat.do(sm3, 2) 
print "##result = ", sm3r

print "-------------------------------------------------------------------------------"
print "##sm0", sm3
print "## repeat.do(sm3, 0, 2) "
sm3r = repeat.do(sm3, 0, 2) 
print "##result = ", sm3r

print "-------------------------------------------------------------------------------"
print "##sm0", sm3
print "## repeat.do(sm3, 2, 2) "
sm3r = repeat.do(sm3, 2, 2) 
print "##result = ", sm3r

