# PURPOSE: (quick overview, to keep the head of the file as a watch window)
#
# SM0:   (0)--- 'a' --->(1)--- 'b' --->(2)--- 'c' --->(3)--- 'e' ---> SUCCESS
#                        |                             ^ 
#                        `------------ 'd' ------------'
#
# SM1:   (4)-- 'a-g' -->(5)--- 'e' --->(6)--- 'f' ---> SUCCESS
#                      /   \
#                     /     \
#                     ` else'
#
# SM2:   (7)--- 'g' --->(8)--- 'e' --->(9)--- 'h' --->(10)--- 'e' ---> SUCCESS
#                        ^                             |
#                        `------------ 'g' ------------'
#
# SM3:   (10)--- 'a' --->(11)--- 'b' --->(12)--- 'c' ---> SUCCESS
#
import sys

from quex.engine.state_machine.core import *
from quex.engine.interval_handling import *

def add_origin(state, StateMachineID_or_StateOriginInfo, StateIdx=None, StoreInputPositionF=False):
    state.origins().add(StateMachineID_or_StateOriginInfo, StateIdx, 
                        StoreInputPositionF, state.is_acceptance())

# (*) set up some state machines
#
# NOTE: We use globally unique state indices!
#

# SM0:   (0)--- 'a' --->(1)--- 'b' --->(2)--- 'c' --->(3)--- 'e' ---> SUCCESS
#                        |                             ^ 
#                        `------------ 'd' ------------'
sm0 = StateMachine()
si0_0 = sm0.init_state_index
si0_1 = sm0.add_transition(si0_0, ord('a'))
si0_2 = sm0.add_transition(si0_1, ord('b'))
si0_3 = sm0.add_transition(si0_2, ord('c'))
sm0.add_transition(si0_1, ord('d'), si0_3)
sm0.add_transition(si0_3, ord('e'), AcceptanceF=True)


# SM1:   (4)-- 'a-g' -->(5)--- 'e' --->(6)--- 'f' ---> SUCCESS
#                      /   \
#                     /     \
#                     ` else'
sm1 = StateMachine()
si1_0 = sm1.init_state_index
si1_1 = sm1.add_transition(si1_0, Interval(ord('a'), ord('g')+1))
sm1.add_transition(si1_0, ord('g'), si1_1)
si1_2 = sm1.add_transition(si1_1, ord('e'))
sm1.add_transition(si1_1, None, si1_1)         # else --> same state
si1_3 = sm1.add_transition(si1_2, ord('f'), AcceptanceF=True)

# SM2:   (7)--- 'g' --->(8)--- 'e' --->(9)--- 'h' --->(10)--- 'e' ---> SUCCESS
#                        ^                             |
#                        `------------ 'g' ------------'
#
sm2 = StateMachine()
si2_0 = sm2.init_state_index
si2_1 = sm2.add_transition(si2_0, ord('g'))
si2_2 = sm2.add_transition(si2_1, ord('e'))
si2_3 = sm2.add_transition(si2_2, ord('h'))
sm2.add_transition(si2_3, ord('g'), si2_1)         
si2_4 = sm2.add_transition(si2_3, ord('e'), AcceptanceF=True)

#
# SM3:   (10)--- 'a' --->(11)--- 'b' --->(12)--- 'c' ---> SUCCESS
#
sm3 = StateMachine()
si3_0 = sm3.init_state_index
si3_1 = sm3.add_transition(si3_0, ord('a'))
si3_2 = sm3.add_transition(si3_1, ord('b'))
si3_3 = sm3.add_transition(si3_2, ord('c'), AcceptanceF=True)


def trivial_sm(Character):
    result = StateMachine()
    result.add_transition(result.init_state_index, ord(Character), AcceptanceF=True)
    return result



