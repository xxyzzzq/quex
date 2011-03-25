#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.state_machine.core import *

if "--hwut-info" in sys.argv:
    print "DFA: Get Trigger Map (intervals --> target states)"
    print "CHOICES: 1, 2, 3, 4, 5, 6, 7;"
    sys.exit(0)

def test(state):
    print "\n## Map: Target Index --> Trigger Set\n"
    # (*) compute the trigger map
    for key, trigger_set in state.transitions().get_map().items():
        print "    %3i <--- %s" % (int(key), repr(trigger_set))

    print "\n## Map: Trigger Intervals (sorted) --> Target Index\n"
    tm = state.transitions().get_trigger_map()
    # (*) print the trigger map entries
    for trigger_interval, target_index in tm:
        print "    %s \t---> %s" % (repr(trigger_interval), repr(target_index))


if "1" in sys.argv:
    # (*) create a couple of number sets and put them as triggers to four 
    #     different target states
    s = State()
    s.add_transition(NumberSet(Interval(0, 10)).union(Interval(20, 30)).union(Interval(40, 50)), 1L)
    s.add_transition(NumberSet(Interval(10, 15)).union(Interval(31, 40)), 2L)
    s.add_transition(NumberSet(Interval(15, 16)).union(Interval(17, 18)), 2L)
    s.add_transition(NumberSet(Interval(55, 60)), 3L)
    s.add_transition(NumberSet(Interval(60,61)), 4L)
    test(s)

elif "2" in sys.argv:
    # (*) special case that appeared during other unit test: only two intervals
    #     are intermediate 'empty intervals' propperly dealt with?    
    s = State()
    s.add_transition(NumberSet([Interval(45, 46), Interval(47, 48)]), 1L)
    test(s)

elif "3" in sys.argv:
    s = State()
    s.add_transition(NumberSet(Interval(46, 47)), 1L)
    s.add_transition(NumberSet(Interval(48, 49)), 1L)
    test(s)
        
elif "4" in sys.argv:
    s = State()
    s.add_transition(NumberSet(Interval(46, 47)), 1L)
    test(s)

    
elif "5" in sys.argv:
    # (*) Intervals with sys.maxint
    s = State()
    s.add_transition(NumberSet(Interval(-sys.maxint, sys.maxint)), 1L)
    test(s)

elif "6" in sys.argv:
    s = State()
    s.add_transition(NumberSet(Interval(-sys.maxint, 0)), 1L)
    test(s)

elif "7" in sys.argv:
    s = State()
    s.add_transition(NumberSet(Interval(0, sys.maxint)), 1L)
    test(s)
