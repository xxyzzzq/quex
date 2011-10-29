#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from copy import deepcopy


import quex.engine.state_machine.repeat as repeat
from   quex.engine.state_machine.core import *
from   quex.engine.state_machine.TEST.test_state_machines import *
import quex.engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.hopcroft_minimization as hopcroft
import quex.engine.state_machine.check.identity as identity_checker

if "--hwut-info" in sys.argv:
    print "DFA: Hopcroft optimization III (state machine combination) "
    print "CHOICES: NEW, ADAPT;"
    sys.exit(0)

if   "NEW"   in sys.argv: CreateNewStateMachineF=True
elif "ADAPT" in sys.argv: CreateNewStateMachineF=False
else:
    print "Require command line arguments: '--hwut-info', 'NEW', or 'ADAPT'"
    sys.exit(-1)

test_i = 0
def test(sm, txt):
    global test_i
    backup_sm = deepcopy(sm)
    print "_______________________________________________________________________________"
    print ("(%i)" % test_i),
    print txt
    optimal_sm = hopcroft.do(sm, CreateNewStateMachineF=CreateNewStateMachineF)
    print optimal_sm
    test_i += 1
    orphan_state_index_list = optimal_sm.get_orphaned_state_index_list()
    if len(orphan_state_index_list) != 0:
        print "ERROR: orphan states found = ", orphan_state_index_list
    if identity_checker.do(backup_sm, optimal_sm) == False:
        print "ERROR: state machines not equivalent"

txt = """
00000() 
      == 'X' ==> 00001
00001() 
      == 'X' ==> 00001
      == 'Y' ==> 00002
      == 'Z' ==> 00003
00002() 
      == 'X' ==> 00001
00003(S, P18)  
      == 'Z' ==> 00004
00004(A, P18)  
"""
sm = StateMachine()
n0 = sm.init_state_index
n1 = sm.add_transition(n0, ord('X'))
sm.add_transition(n1, ord('X'), n1)
n2 = sm.add_transition(n1, ord('Y'))
n3 = sm.add_transition(n1, ord('Z'))

n2 = sm.add_transition(n2, ord('X'), n1)

n4 = sm.add_transition(n3, ord('Z'))

sm.states[n3].set_input_position_store_f()
sm.states[n4].set_acceptance(True)
sm.states[n4].set_input_position_restore_f(True)
sm.mark_state_origins()
test(sm, txt)
