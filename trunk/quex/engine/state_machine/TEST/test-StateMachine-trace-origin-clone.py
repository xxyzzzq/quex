#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.sequentialize 
from quex.engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "Tracing origin: Cloning"
    sys.exit(0)

sm0.mark_state_origins()    
sm1.mark_state_origins()    
sm2.mark_state_origins()    
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
print sm3
print sm3.clone()

