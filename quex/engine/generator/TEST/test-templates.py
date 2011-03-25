#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.engine.state_machine.compression.templates as templates
from   quex.engine.state_machine.core                  import StateMachine, State
import quex.engine.generator.template_coder            as coder
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.languages.address         import get_plain_strings
import quex.engine.generator.state_router              as state_router  
import quex.engine.generator.languages.cpp             as cpp
from   quex.engine.generator.state_machine_decorator   import StateMachineDecorator
from   quex.input.setup import setup as Setup
from   generator_test   import __Setup_init_language_database

if "--hwut-info" in sys.argv:
    print "Basic Template Compression Test;"
    print "CHOICES: 1, 2;"
    sys.exit(0)

# Buffer limit code is required in order to choose between
# 'direct drop out' and 'drop out' in state transition map.
Setup.buffer_limit_code = 0
Setup.path_limit_code   = 1
__Setup_init_language_database("Cpp")

# A state machine decorator is required for the code generation.
# Create a default one
sm = StateMachine()

sm.states = {
        1L:   State(),
        2L:   State(),
        3L:   State(),
        100L: State(),
        200L: State(),
        202L: State(),
        300L: State(),
        400L: State(),
        500L: State(),
        }
# print sm.states.keys()
for state_index in sm.states.keys():
    sm.add_transition(state_index, 1L, 202L)

DSM = StateMachineDecorator(sm, "Test", [], False, False)
# print DSM.sm().states.keys()


if "1" in sys.argv:
    combination = templates.TemplateCombination([100L], [200L, 202L])
    combination.append(-sys.maxint, 10, None)
    combination.append(8,   9,          [1L, None, 2L])
    combination.append(9,  10,          [1L, 3L,   2L])
    combination.append(10, 11,          100L)
    combination.append(11, 12,          -2)
    combination.append(12, 13,          None)
    combination.append(14, sys.maxint,  [2L, 3L,   1L])

else:
    combination = templates.TemplateCombination([100L], [200L, 202L, 300L, 400L, 500L])
    combination.append(-sys.maxint, 10, [1L, None, 1L, 2L,   2L, 2L])
    combination.append(10,  sys.maxint, [2L, 3L,   1L, None, 2L, 2L])

x = coder._do([combination], DSM)

state_info_list  = state_router.get_info(x[1], None)
router           = state_router.do(state_info_list)
state_router_txt = "".join(router.code)

print "--(Transition Targets)--------------------------------------------------"
print
print "".join(cpp.__local_variable_definitions(variable_db.get()))
print
print "--(Template Code)-------------------------------------------------------"
print
print "".join(get_plain_strings(x[0]))
print
print "--(State Router)--------------------------------------------------------"
print
print state_router_txt
print

sys.exit(0)

