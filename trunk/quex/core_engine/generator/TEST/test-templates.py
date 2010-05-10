#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.core_engine.state_machine.compression.templates as templates
import quex.core_engine.generator.template_coder            as coder
from   quex.core_engine.state_machine.core                  import StateMachine, State
from   quex.core_engine.generator.state_machine_decorator   import StateMachineDecorator

if "--hwut-info" in sys.argv:
    print "Basic Template Compression Test"
    sys.exit(0)


# A state machine decorator is required for the code generation.
# Create a default one
DSM = StateMachineDecorator(StateMachine(), "Test", [], False, False)

combination = templates.Combination([100L], [200L, 202L])

combination.append(-sys.maxint, 10, 1L)
combination.append(10, sys.maxint,  2L)

print coder.do([combination], DSM)

sys.exit(0)

combination.append(10, 20,          [2L, 3L, 4L])
combination.append(20, 30,          2L)
combination.append(30, 40,          -1)
combination.append(40, 50,          100L)
