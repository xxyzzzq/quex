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

from quex.core_engine.interval_handling import NumberSet, Interval
from quex.core_engine.state_machine.core import StateInfo

import quex.core_engine.generator.state_transition_coder as state_transition_coder

if "--hwut-info" in sys.argv:
    print "Single State: Extensive Transition Code Generation"
    sys.exit(0)


# Create a large number of intervals with sizes 1 to 4. 
state = StateInfo()
interval_start = 0
interval_end   = -1
# initialize pseudo random generator: produces always the same numbers.
random.seed(110270)   # must set the seed for randomness, otherwise system time
#                     # is used which is no longer deterministic.
for i in range(300):
    interval_end = interval_start + int(random.random() * 4) + 1
    state.add_transition(Interval(interval_start, interval_end), long(i % 24))
    interval_start = interval_end

function = "def example_func(input):\n" + state_transition_coder.do("Python", "", state, -1, False)
exec(function)

differences = []    
for number in range(interval_end):
    result_state_idx = state.get_result_state_index(number)
    if result_state_idx == None: result_state_idx = -1
    sys.stdout.write("%i %s %s\n" % (number, repr(example_func(number)), repr(result_state_idx)))
    if example_func(number) != result_state_idx:
        differences.append(number)

print "# errors = ", differences    


