#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.core_engine.state_machine.compression.paths     as paths    
from   quex.core_engine.state_machine.core                  import StateMachine, State
import quex.core_engine.state_machine.index                 as index                  
import quex.core_engine.generator.paths_coder               as coder
import quex.core_engine.generator.languages.cpp             as cpp
from   quex.core_engine.generator.state_machine_decorator   import StateMachineDecorator
from   quex.core_engine.interval_handling                   import *
from   quex.input.setup import setup as Setup

if "--hwut-info" in sys.argv:
    print "Basic Path Compression Test;"
    print "CHOICES: Single, Multiple, NonUniform;"
    sys.exit(0)

# Buffer limit code is required in order to choose between
# 'direct drop out' and 'drop out' in state transition map.
Setup.buffer_limit_code = 0

# A state machine decorator is required for the code generation.
# Create a default one
sm = StateMachine()

# print sm.states.keys()
for state_index in sm.states.keys():
    sm.add_transition(state_index, 1L, 202L)

SMD = StateMachineDecorator(sm, "Test", [], False, False)
# print SMD.sm().states.keys()

def get_path(Sequence, Skeleton, UniformF=True):
    global sm

    state_index = index.get()

    trigger_map = {}
    for key, interval_list in Skeleton.items():
        trigger_map[key] = NumberSet(interval_list)

    sm.states[state_index] = State()
    char = Sequence[0]
    path = paths.CharacterPath(state_index, trigger_map, ord(char))
    state_index = sm.add_transition(state_index, ord(char))

    for i, char in enumerate(Sequence[1:]):
        path.append(state_index, ord(char))
        # Make sure that a state like this exists inside the state machine
        state_index = sm.add_transition(state_index, ord(char))
        if not UniformF and i % 2 == 1: sm.states[state_index].set_acceptance()
    path.set_end_state_index(state_index)

    return path

skeleton = { 
        1: [Interval(10, 11), Interval(64, 65)],
        2: [Interval(20, 21)],
}
if "Single" in sys.argv:
    path_list = [ get_path("congo", skeleton) ]

elif "Multiple" in sys.argv:
    path_list = [ get_path("otto", skeleton),
                  get_path("grunibaldi", skeleton),
                  get_path("fritz", skeleton) ]

elif "NonUniform" in sys.argv:
    path_list = [ get_path("otto", skeleton),
                  get_path("grunibaldi", skeleton, UniformF=False),
                  get_path("fritz", skeleton) ]


x = coder._do(path_list, SMD)

print "--(Path Definitions)----------------------------------------------------"
print
print cpp.__local_variable_definitions(x[0])
print
print "--(Pathwalker Code)-----------------------------------------------------"
print
print "".join(x[1])
print
print "--(Involved State Indices)----------------------------------------------"
print
print x[2]
print

sys.exit(0)

