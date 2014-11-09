#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.state_machine.core import *
import quex.engine.state_machine.construction.parallelize 
from quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.algebra.reverse         as reverse

if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Inverse"
    sys.exit(0)

def test(sm):
    print "-------------------------------------------------------------------------------"
    print "sm       = ",      sm
    sm = reverse.do(sm)
    print "inverse  = ", sm 

test(sm0)
test(sm1)
test(sm2)    
test(sm3)    
