# TEST: Generation of state machine based on a loop.
#
# The generation of a loop state machine happens based on a loop lexatom
# set 'L' and optionally parallel state machines. As long as lexatoms in from 
# the set 'L' appear, the loop continues. Lexatoms may also trigger a walk
# along the parallel state machines, that may match and cause specific 
# actions in the according terminals.
#
# This test investigates the generation of the state machines only under three
# circumstances expressed as CHOICES:
#
#   -- 'Plain' loop generation, i.e. no parallel state machines.
#   -- 'SMX', i.e. a loop with parallel state machines that do not intersect.
#   -- 'SML', i.e. a loop with parallel state machines that do not intersect.
#   -- 'Both', i.e. 'SMX' and 'SML'.
#
# (C) Frank-Rene Schaefer
#------------------------------------------------------------------------------
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.output.core.loop                as     loop
from   quex.input.files.parser_data.counter import ParserDataLineColumn, \
                                                   CountInfo
from   quex.engine.state_machine.core       import StateMachine  
from   quex.engine.misc.interval_handling   import NumberSet, \
                                                   NumberSet_All
from   quex.engine.loop_counter             import LoopCountOpFactory
from   quex.blackboard                      import E_CharacterCountType, \
                                                   setup as Setup

if "--hwut-info" in sys.argv:
    print "Loop: Base state machine."
    print "CHOICES: Plain, SMX, SML, Both;"

def test(cmap, SM_list=[]):
    Setup.buffer_codec.source_set = NumberSet_All()
    cc_factory = LoopCountOpFactory(cmap, NumberSet.from_range(0, 100))
    sm         = loop._get_state_machine(cc_factory, SM_list, 
                                         IidBeyond   = 8888, 
                                         IidBeyondRs = 7777, 
                                         IidLoop     = 6666)
    print sm.get_string(Option="hex")

    # print sm.get_graphviz_string(Option="hex")

def get_setup(L0, L1, FSM0, FSM1, FSM2):
    # SPECIALITIES: -- sm0 and sm1 have an intersection between their first 
    #                  transition.
    #               -- sm1 transits further upon acceptance.
    #               -- both first transitions 'touch' the borders of the loop.
    #               -- sm2 has only one transition.
    cmap = [
        CountInfo(0, E_CharacterCountType.COLUMN, 0, NumberSet.from_range(L0, L1)),
    ]

    # Generate State Machine that does not have any intersection with 
    # the loop transitions.
    sm0 = StateMachine()
    si = sm0.add_transition(sm0.init_state_index, FSM0)
    si = sm0.add_transition(si, NumberSet.from_range(0xA, 0xB), AcceptanceF=True)
    sm0.states[si].mark_acceptance_id(sm0.get_id())

    sm1 = StateMachine()
    si0 = sm1.add_transition(sm1.init_state_index, FSM1)
    si  = sm1.add_transition(si0, NumberSet.from_range(0xA, 0xB), AcceptanceF=True)
    sm1.states[si].mark_acceptance_id(sm1.get_id())
    si  = sm1.add_transition(si, NumberSet.from_range(0xE, 0xF), si0)
    sm1.states[si].mark_acceptance_id(sm1.get_id())

    sm2 = StateMachine()
    si = sm2.add_transition(sm2.init_state_index, FSM2, AcceptanceF=True)
    sm2.states[si].mark_acceptance_id(sm2.get_id())

    return cmap, [sm0, sm1, sm2]

if "Plain" in sys.argv:
    # No parallel state machines
    test([
        CountInfo(0, E_CharacterCountType.COLUMN,     0, NumberSet.from_range(0,    0x10)),
        CountInfo(1, E_CharacterCountType.LINE,       1, NumberSet.from_range(0x20, 0x30)),
        CountInfo(2, E_CharacterCountType.GRID,       2, NumberSet.from_range(0x40, 0x50)),
        CountInfo(3, E_CharacterCountType.WHITESPACE, 3, NumberSet.from_range(0x60, 0x70)),
    ])

elif "SMX" in sys.argv:
    # Three state machines (no one intersects on first transition with loop):
    # 
    # Loop:               0x0F                  
    # First Trans. sm0:         0x10-0x1A
    # First Trans. sm1:              0x1A-0x1F
    # First Trans. sm2:                         0x20
    #
    cmap, sm_list = get_setup(0x0F, 0x10, 
                              NumberSet.from_range(0x10, 0x1B), 
                              NumberSet.from_range(0x1A, 0x20), 
                              NumberSet.from_range(0x20, 0x21))

    for sm in sm_list:
        test(cmap, [sm])
    test(cmap, sm_list)

elif "SML" in sys.argv:
    # Three state machines (intersect completely on first transition with loop):
    # 
    # Loop:               0x00          -       0x20                  
    # First Trans. sm0:         0x10-0x1A
    # First Trans. sm1:              0x1A-0x1F
    # First Trans. sm2:                         0x20
    #
    cmap, sm_list = get_setup(0x00, 0x21, 
                              NumberSet.from_range(0x10, 0x1B), 
                              NumberSet.from_range(0x1A, 0x20), 
                              NumberSet.from_range(0x20, 0x21))

    for sm in sm_list:
        test(cmap, [sm])
    test(cmap, sm_list)

