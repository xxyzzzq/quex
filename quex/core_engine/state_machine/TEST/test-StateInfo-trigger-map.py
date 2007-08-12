#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *

if "--hwut-info" in sys.argv:
    print "DFA: Get Trigger Map (intervals --> target states)"
    sys.exit(0)

def test(sm):
    # (*) compute the trigger map
    tm = sm.get_trigger_map()
    # (*) print the trigger map entries
    for trigger_interval, target_index in tm:
	if target_index == None:
	    print trigger_interval.gnuplot_string(-1) + "\n"
	else:	
	    print trigger_interval.gnuplot_string(target_index) + "\n"


# (*) create a couple of number sets and put them as triggers to four 
#     different target states
print "#---------------------------------------------------------------------------------------"
s = StateInfo()
s.add_transition(NumberSet(Interval(0, 10)).union(Interval(20, 30)).union(Interval(40, 50)), 1L)
s.add_transition(NumberSet(Interval(10, 15)).union(Interval(31, 40)), 2L)
s.add_transition(NumberSet(Interval(15, 16)).union(Interval(17, 18)), 2L)
s.add_transition(NumberSet(Interval(55, 60)), 3L)
s.add_transition(NumberSet(Interval(60,61)), 4L)

print "# in gnuplot: plot [0:70] \"tmp\" w l" 
test(s)

# (*) special case that appeared during other unit test: only two intervals
#     are intermediate 'empty intervals' propperly dealt with?    
print "#---------------------------------------------------------------------------------------"
s = StateInfo()
s.add_transition(NumberSet([Interval(45, 46), Interval(47, 48)]), 1L)
test(s)

print "#---------------------------------------------------------------------------------------"
s = StateInfo()
s.add_transition(NumberSet(Interval(46, 47)), 1L)
s.add_transition(NumberSet(Interval(48, 49)), 1L)
test(s)
	
# (*) special case: only one interval at all
s = StateInfo()
s.add_transition(NumberSet(Interval(46, 47)), 1L)
test(s)
    
