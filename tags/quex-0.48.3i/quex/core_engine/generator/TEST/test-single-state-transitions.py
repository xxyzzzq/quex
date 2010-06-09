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

from quex.core_engine.interval_handling  import NumberSet, Interval
from quex.core_engine.state_machine.core import State, StateMachine

import quex.core_engine.generator.languages.core as languages
import quex.core_engine.generator.state_coder.transition_block as transition_block
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

if "--hwut-info" in sys.argv:
    print "Single State: Transition Code Generation;"
    print "CHOICES: A, B, C;"
    sys.exit(0)

state = State()

if "A" in sys.argv:
    state.add_transition(NumberSet([Interval(10,20),    Interval(195,196)]),  1L)
    state.add_transition(NumberSet([Interval(51,70),    Interval(261,280)]),  2L)
    state.add_transition(NumberSet([Interval(90,100),   Interval(110,130)]),  3L)
    state.add_transition(NumberSet([Interval(150,151),  Interval(151,190)]),  4L)
    state.add_transition(NumberSet([Interval(190,195),  Interval(21,30)]),    5L) 
    state.add_transition(NumberSet([Interval(197, 198), Interval(198, 198)]), 6L)
    state.add_transition(NumberSet([Interval(200,230),  Interval(231,240)]),  7L)
    state.add_transition(NumberSet([Interval(250,260),  Interval(71,80), Interval(71,71)]),  8L)
    
    interval_end = 300

elif "B" in sys.argv:
    interval_start = 0
    interval_end   = -1
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.
    max_number = 300
    for i in range(4000):
        interval_size      = int(random.random() * 4) + 1
        target_state_index = long(random.random() * 10)
        interval_end = interval_start + interval_size
        state.add_transition(Interval(interval_start, interval_end), target_state_index)
        interval_start = interval_end

elif "C" in sys.argv:
    interval_start = 0
    interval_end   = -1
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.
    target_state_index = long(0)
    for i in range(1000):
        if random.random() > 0.75:
            interval_size      = int(random.random() * 3) + 1
            target_state_index = long(random.random() * 5)

            interval_end = interval_start + interval_size
            state.add_transition(Interval(interval_start, interval_end), target_state_index)
            interval_start = interval_end
        else:
            target_state_index = long(random.random() * 5)
            for i in range(0, int(random.random() * 5) + 2):
                state.add_transition(Interval(interval_start, interval_start + 1), target_state_index)
                interval_start += 1 + int(random.random() * 2)

# Make sure, that the 'goto state' is transformed into 'return index of target state'
languages.db["Python"]["$goto"] = lambda x, y: "return %s" % repr(y)   

dsm = StateMachineDecorator(StateMachine(), "UnitTest", [], False, False)
function  = "def example_func(input):\n"
function += "".join(transition_block.do(state.transitions().get_trigger_map(), 
                                        None, dsm))
function  = function.replace("_-1_", "_MINUS_1_")

# line_n = 0
# for line in function.split("\n"):
#     print "##%i" % line_n, line
#     line_n += 1

exec(function)
differences = []    
for number in range(interval_end):
    expected_state_index = state.transitions().get_resulting_target_state_index(number)
    if expected_state_index == None: expected_state_index = -1
    actual_state_index = example_func(number)
    if actual_state_index == None: actual_state_index = -1
    sys.stdout.write("%i %s %s\n" % (number, repr(actual_state_index), repr(expected_state_index)))
    if actual_state_index != expected_state_index:
        differences.append(number)

print "# errors = ", differences    


