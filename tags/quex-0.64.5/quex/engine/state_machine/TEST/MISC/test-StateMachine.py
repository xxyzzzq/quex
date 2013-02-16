#! /usr/bin/env python
import sys
sys.path.append("../")

from core import *


# (*) implement a simple state machine
#
#     (0)--- h --->(1)--- e --->(2)--- l --->(3)--- l --->(4)--- o --->SUCCESS
#      |            |            |            |            |
#      FAIL         FAIL         FAIL         FAIL         FAIL
#
sm = StateMachine()

state_idx = sm.init_state_index
state_idx = sm.add_transition(state_idx, ord('h')) # return created target_idx
state_idx = sm.add_transition(state_idx, ord('e'))
state_idx = sm.add_transition(state_idx, ord('l'))
state_idx = sm.add_transition(state_idx, ord('l'))
state_idx = sm.add_transition(state_idx, ord('o'), RaiseSuccessF=True)

print sm
