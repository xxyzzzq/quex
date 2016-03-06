#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.state_machine.TEST.test_state_machines import sm3
import quex.engine.state_machine.TEST.helper_state_machine_shapes as sms
from   quex.engine.state_machine.core                     import *
import quex.engine.state_machine.construction.repeat      as repeat
import quex.engine.state_machine.algorithm.nfa_to_dfa     as nfa_to_dfa

if "--hwut-info" in sys.argv:
    print "NFA: Conversion to DFA (subset construction)"
    sys.exit(0)
    
print "_______________________________________________________________________________"
plot_txt = """

          .- 11 ->( 1 )-- 22 ->( 2 )
         /          | eps
        /           v     
     ( 0 )        ( 5 )-- 66 ->( 6 )
        \           n
         \          | eps 
          '- 33 ->( 3 )-- 44 ->( 4 )

The epsilon closures depend on the direction:
    * from 3: epsilon closure (3, 5)
    * from 1: epsilon closure (1, 5)
=> State '5' is merged into two resulting states.
"""
sm = StateMachine()
sms.line(sm, sm.init_state_index, (0x11, 1), (0x22, 2))
sms.line(sm, sm.init_state_index, (0x33, 3), (0x44, 4))
sms.line(sm, 5,                              (0x66, 6))
sms.line(sm, 1, (None, 5))
sms.line(sm, 3, (None, 5))

dfa = nfa_to_dfa.do(sm)
print plot_txt
print dfa.get_string(NormalizeF=False, Option="hex")

print "_______________________________________________________________________________"
plot_txt = """

        ( 1 )-- 22 --->( 2 )-- 33 --->( 3 )-- 55 --->( 5 )
          n    .<- 33 --'     
          | .--'           
        ( 0 )-- eps -->( 4 )-- 66 --->( 6 )

State '4' is be joined into epsilon closure with '0' from beginning.  Later,
when it is detected that '2' triggers on the same trigger set to '0' and '3',
'0' joined with '3'.
"""
sm = StateMachine()
sms.line(sm, sm.init_state_index, (0x11, 1), (0x22, 2), (0x33, 3), (0x55, 5))
sms.line(sm, sm.init_state_index, (None, 4))
sms.line(sm, 2, (0x33, sm.init_state_index))
sms.line(sm, 4, (0x66, 6))

dfa = nfa_to_dfa.do(sm)
print plot_txt
print dfa.get_string(NormalizeF=False, Option="hex")

