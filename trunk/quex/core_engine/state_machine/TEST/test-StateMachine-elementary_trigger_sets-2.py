#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.interval_handling import *
from quex.core_engine.state_machine.core import *

if "--hwut-info" in sys.argv:
    print "NFA: Get elementary trigger sets II"
    sys.exit(0)

# (*) Special case that caused trouble before: two states
#     trigger on the same trigger to the same target state.
sm = StateMachine()
sm.add_transition(36L, 98, 100L)
sm.add_transition(37L, 98, 100L)

print "states machine = ", sm

# (*) compute the elementary trigger set
epsilon_closure_db = sm.get_epsilon_closure_db()
ets = sm.get_elementary_trigger_sets([36, 37], epsilon_closure_db)
print "elementary trigger sets = ", ets
i = 10
for target_indices, trigger_set in ets:
    i += 1
    print trigger_set.gnuplot_string(i)


# (*) Another special case
sm = StateMachine()
sm.add_transition(36L, Interval(98, 100), 100L)
sm.add_transition(37L, 98, 100L)

print "states machine = ", sm

# (*) compute the elementary trigger set
epsilon_closure_db = sm.get_epsilon_closure_db()
ets = sm.get_elementary_trigger_sets([36, 37], epsilon_closure_db)
print "elementary trigger sets = ", ets
i = 10
for target_indices, trigger_set in ets:
    i += 1
    print trigger_set.gnuplot_string(i)
            
