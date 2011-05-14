#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.state_machine.core import *

if "--hwut-info" in sys.argv:
    print "NFA: Get elementary trigger sets (target index --> trigger sets)"
    sys.exit(0)

# (*) create a couple of number sets and put them as triggers to four 
#     different target states
sm = StateMachine()
sm.add_transition(10L,
                  NumberSet(Interval(0, 10)).union(Interval(20, 30)).union(Interval(40, 50)),
                  1L)
sm.add_transition(10L,
                  NumberSet(Interval(5, 10)).union(Interval(21, 29)),
                  2L)
sm.add_transition(10L,
                  NumberSet(Interval(11, 20)).union(Interval(22, 23)).union(Interval(50, 60)),
                  3L)
sm.add_transition(10L,
                  NumberSet(Interval(35, 42)),
                  4L)

sm.create_new_state(StateIdx=1)
sm.create_new_state(StateIdx=2)
sm.create_new_state(StateIdx=3)
sm.create_new_state(StateIdx=4)

print "# in gnuplot: plot [0:70] \"tmp\" w l" 

for key, trigger_set in sm.states[10].transitions().get_map().items():
    print trigger_set.gnuplot_string(key)

# (*) compute the elementary trigger set
epsilon_closure_db = sm.get_epsilon_closure_db()
ets = sm.get_elementary_trigger_sets([10], epsilon_closure_db)
i = 10
for target_indices, trigger_set in ets:
    i += 1
    print trigger_set.gnuplot_string(i)
