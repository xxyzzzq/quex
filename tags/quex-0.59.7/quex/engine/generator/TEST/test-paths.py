#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.engine.state_machine.compression.paths     as paths    
from   quex.engine.state_machine.core                  import StateMachine, State
import quex.engine.state_machine.index                 as index                  
import quex.engine.generator.paths_coder               as coder
import quex.engine.generator.languages.cpp             as cpp
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.languages.address         import get_plain_strings
from   quex.engine.generator.state_machine_decorator   import StateMachineDecorator
from   quex.engine.interval_handling                   import *
from   quex.blackboard import setup as Setup
from   generator_test   import __Setup_init_language_database

if "--hwut-info" in sys.argv:
    print "Basic Path Compression Test;"
    print "CHOICES: Single, Multiple, NonUniform, NonUniform2;"
    sys.exit(0)

# Buffer limit code is required in order to choose between
# 'direct drop out' and 'drop out' in state transition map.
Setup.buffer_limit_code = 0
Setup.path_limit_code   = 1
__Setup_init_language_database("Cpp")

# A state machine decorator is required for the code generation.
# Create a default one
sm = StateMachine()

# print sm.states.keys()
for state_index in sm.states.keys():
    sm.add_transition(state_index, 1L, 202L)

SMD = StateMachineDecorator(sm, "Test", [], False, False)
# print SMD.sm().states.keys()

dummy_char = ord('a') - 1
def get_path(Sequence, Skeleton, UniformF=True):
    global dummy_char
    global sm
    
    dummy_char += 1

    state_index = index.get()

    trigger_map = {}
    for key, interval_list in Skeleton.items():
        trigger_map[key] = NumberSet(interval_list)

    sm.states[state_index] = State()
    char = Sequence[0]
    path = paths.CharacterPath(state_index, trigger_map, ord(char))
    sm.add_transition(sm.init_state_index, dummy_char, state_index)
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
    x = coder._do(path_list, SMD, UniformOnlyF=True)

elif "Multiple" in sys.argv:
    path_list = [ get_path("otto", skeleton),
                  get_path("grunibaldi", skeleton),
                  get_path("fritz", skeleton) ]
    x = coder._do(path_list, SMD, UniformOnlyF=True)

elif "NonUniform" in sys.argv:
    path_list = [ get_path("otto", skeleton),
                  get_path("grunibaldi", skeleton, UniformF=False),
                  get_path("fritz", skeleton) ]
    x = coder._do(path_list, SMD, UniformOnlyF=False)

elif "NonUniform2" in sys.argv:
    # Consider only uniform path's were there is a non-uniform path
    path_list = [ get_path("otto", skeleton),
                  get_path("grunibaldi", skeleton, UniformF=False),
                  get_path("fritz", skeleton) ]

    # The state machine has been setup during 'get_path()'
    code, state_list = coder.do(SMD, UniformOnlyF=True)
    x = [code, state_list]

print "--(Path Definitions)----------------------------------------------------"
print
print "".join(cpp.__local_variable_definitions(variable_db.get()))
print
print "--(Pathwalker Code)-----------------------------------------------------"
print
print "".join(get_plain_strings(x[0]))
print
print "--(Involved State Indices)----------------------------------------------"
print
print x[1]
print

sys.exit(0)

