#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.engine.state_machine.setup_post_context as setup_post_context
import quex.engine.state_machine.setup_pre_context as setup_pre_context 
import quex.engine.state_machine.setup_border_conditions as setup_border_conditions 
import quex.engine.state_machine.nfa_to_dfa as nfa_to_dfa
import quex.engine.state_machine.hopcroft_minimization as hopcroft

from quex.engine.state_machine.TEST.test_state_machines import *


if "--hwut-info" in sys.argv:
    print "StateMachine Operations: Append Post Condition"
    sys.exit(0)


def test(Idx, sm_pre, sm, sm_post, BOF_F, EOF_F):    
    result = sm.clone()
    print "##-- %i -----------------------------------------------------------------------" % Idx
    if sm_pre is not None: 
        setup_pre_context.do(result, sm_pre)
        print " -- pre-condition  = True"
    else:
        print " -- pre-condition  = False"
        
    if sm_post is not None:
        setup_post_context.do(result, sm_post)
        print " -- post-condition = True"
    else:
        print " -- post-condition = False"
    
    print " -- begin of file  = ", BOF_F
    print " -- end of file    = ", EOF_F

    # print "HOPCROFT = ", result
    result = setup_border_conditions.do(result, BOF_F, EOF_F)
    #
    # print "EXPRESSION = ", result
    # print "POST CONDITION = ", post_sm
    # print "APPENDED = ", result
    result = nfa_to_dfa.do(result)
    # print "DFA = ", result
    result = hopcroft.do(result)
    #
    #
    print
    print "result sm.id     = ", result.get_id()
    if result.core().pre_context_sm() is not None:
        print "result pre sm.id = ", result.core().pre_context_sm().get_id()
    print "result = ", result
    print "trivially pre-conditioned = ", result.core().pre_context_begin_of_line_f()

    # sys.exit(-1)

tiny0 = StateMachine()
tiny0.add_transition(tiny0.init_state_index, ord('0'), AcceptanceF=True)
tiny1 = StateMachine()
tiny1.add_transition(tiny1.init_state_index, ord('1'), AcceptanceF=True)
tiny2 = StateMachine()
tiny2.add_transition(tiny2.init_state_index, ord('2'), AcceptanceF=True)

i = -1
for flag_k in range(0, 4):
    sm_pre  = None
    sm_post = None
    if flag_k & 2 == 2: sm_pre  = tiny0.clone() # None
    if flag_k & 1 == 1: sm_post = tiny2.clone()
    sm = tiny1.clone()

    for flag_i in range(0, 4):
        i += 1
        bof_f = flag_i & 2 == 2
        eof_f = flag_i & 1 == 1
        test(i, sm_pre, sm, sm_post, bof_f,  eof_f)    
    
   

