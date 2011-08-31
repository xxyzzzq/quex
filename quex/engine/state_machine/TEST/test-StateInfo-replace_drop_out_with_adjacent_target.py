#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.state_machine.core import *
from quex.blackboard                import E_StateIndices

if "--hwut-info" in sys.argv:
    print "Pseudo Ambigous Post Condition: Replace Drop-Out with Adjacent Target"
    sys.exit(0)

if "--show" in sys.argv: show_mode_f = True
else:                    show_mode_f = False

def output_trigger_map(tm, BeforeF):
    # (*) print the trigger map entries
    if BeforeF: filestem = "tmp0"
    else:       filestem = "tmp1"

    if show_mode_f: 
        fh = open(filestem + ".gpl", "w")
        fh.write("# part = %s.gpl" % filestem)
    else:           
        fh = sys.stdout

    for trigger_interval, target_index in tm:
        if target_index is E_StateIndices.DROP_OUT:
            fh.write(trigger_interval.gnuplot_string(-1) + "\n")
        else:   
            fh.write(trigger_interval.gnuplot_string(target_index) + "\n")

def test(state):
    # (*) compute the trigger map
    output_trigger_map(state.transitions().get_trigger_map(), BeforeF=True)
    state.transitions().replace_drop_out_target_states_with_adjacent_targets()
    output_trigger_map(state.transitions().get_trigger_map(), BeforeF=False)


# (*) create a couple of number sets and put them as triggers to four 
#     different target states
print "#---------------------------------------------------------------------------------------"
s = State()
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
s = State()
s.add_transition(NumberSet([Interval(45, 46), Interval(47, 48)]), 1L)
test(s)

print "#---------------------------------------------------------------------------------------"
s = State()
s.add_transition(NumberSet(Interval(46, 47)), 1L)
s.add_transition(NumberSet(Interval(48, 49)), 1L)
test(s)
        
# (*) special case: only one interval at all
s = State()
s.add_transition(NumberSet(Interval(46, 47)), 1L)
test(s)
    

