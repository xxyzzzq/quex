#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.sequentialize as sequentialize 
from quex.core_engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine: Cloning"
    sys.exit(0)
    
print "------------------------------------------"
print sm0
print sm0.clone()

print "------------------------------------------"
print sm1
print sm1.clone()

print "------------------------------------------"
print sm2
print sm2.clone()

print "------------------------------------------"
sm3.mark_state_origins()
print sm3
print sm3.clone()


print Interval(ord('a'), ord('g')+1).inverse()
