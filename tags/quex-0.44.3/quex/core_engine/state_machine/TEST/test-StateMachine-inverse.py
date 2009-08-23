#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.parallelize 
from quex.core_engine.state_machine.TEST.test_state_machines import *

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Inverse"
    sys.exit(0)

def test(sm):
    print "-------------------------------------------------------------------------------"
    print "sm       = ",      sm
    sm = sm.get_inverse()
    print "inverse  = ", sm 

test(sm0)
test(sm1)
test(sm2)    
test(sm3)    
