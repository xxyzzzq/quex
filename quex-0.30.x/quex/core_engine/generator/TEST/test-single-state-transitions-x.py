#! /usr/bin/env python
# PURPOSE: Test the code generation for number sets. Two outputs are generated:
#
#           (1) stdout: containing value pairs (x,y) where y is 1.8 if x lies
#               inside the number set and 1.0 if x lies outside the number set.
#           (2) 'tmp2': containing the information about the number set under
#               consideration.
#
# The result is best viewed with 'gnuplot'. Call the program redirect the stdout
# to file 'tmp2' and type in gnuplot:
#
#         > plot [][0.8:2] "tmp2" w l, "tmp" w p
################################################################################
import sys
import os
import random
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.input.setup import setup as Setup
import quex.core_engine.generator.languages.core as languages
Setup.language_db = languages.db["Python"]

from quex.core_engine.interval_handling import NumberSet, Interval
from quex.core_engine.state_machine.core import State, StateMachine

import quex.core_engine.generator.languages.core as languages
import quex.core_engine.generator.transition_block    as transition_block
from   quex.core_engine.generator.state_machine_coder import StateMachineDecorator

if "--hwut-info" in sys.argv:
    print "Single State: Extensive Transition Code Generation"
    sys.exit(0)

# Create a large number of intervals with sizes 1 to 4. 
state = State()
interval_start = 0
interval_end   = -1
# initialize pseudo random generator: produces always the same numbers.
random.seed(110270)   # must set the seed for randomness, otherwise system time
#                     # is used which is no longer deterministic.
for i in range(4000):
    interval_end = interval_start + int(random.random() * 4) + 1
    state.add_transition(Interval(interval_start, interval_end), long(i % 24))
    interval_start = interval_end

languages.db["Python"]["$goto"] = lambda x, y: "return %s" % repr(y)   

dsm = StateMachineDecorator(StateMachine(), "UnitTest", [], False, False)
function = "def example_func(input):\n" + transition_block.do(state, -1, False, dsm)
exec(function)

differences = []    
transitions = state.transitions()
for number in range(interval_end):
    result_state_idx = transitions.get_resulting_target_state_index(number)
    if result_state_idx == None: result_state_idx = -1
    sys.stdout.write("%i %s %s\n" % (number, repr(example_func(number)), repr(result_state_idx)))
    if example_func(number) != result_state_idx:
        differences.append(number)

print "# errors = ", differences    


