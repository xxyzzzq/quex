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
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.core_engine.interval_handling import NumberSet, Interval
from quex.core_engine.state_machine.core import StateInfo

import quex.core_engine.generator.languages.core         as languages
import quex.core_engine.generator.state_transition_coder as state_transition_coder

if "--hwut-info" in sys.argv:
    print "Single State: Transition Code Generation"
    sys.exit(0)

state = StateInfo()
state.add_transition(NumberSet([Interval(10,20),    Interval(195,196)]),  1L)
state.add_transition(NumberSet([Interval(51,70),    Interval(261,280)]),  2L)
state.add_transition(NumberSet([Interval(90,100),   Interval(110,130)]),  3L)
state.add_transition(NumberSet([Interval(150,151),  Interval(151,190)]),  4L)
state.add_transition(NumberSet([Interval(190,195),  Interval(21,30)]),    5L) 
state.add_transition(NumberSet([Interval(197, 198), Interval(198, 198)]), 6L)
state.add_transition(NumberSet([Interval(200,230),  Interval(231,240)]),  7L)
state.add_transition(NumberSet([Interval(250,260),  Interval(71,80), Interval(71,71)]),  8L)


function = "def example_func(input):\n" + state_transition_coder.do(languages.db["Python"], "", state, -1, False)
#print "#" + function.replace("\n", "\n#")
exec(function)

differences = []    
for number in range(300):
    result_state_idx = state.get_result_state_index(number)
    if result_state_idx == None: result_state_idx = -1
    sys.stdout.write("%i %s %s\n" % (number, repr(example_func(number)), repr(result_state_idx)))
    if example_func(number) != result_state_idx:
        differences.append(number)

print "# errors = ", differences    


