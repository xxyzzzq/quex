#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling        import *
import quex.engine.state_machine.core          as core
import quex.engine.state_machine.algorithm.nfa_to_dfa as nfa_to_dfa
import quex.engine.analyzer.mega_state.path_walker.core          as paths 
from   quex.engine.analyzer.core               import Analyzer
from   quex.blackboard                         import E_EngineTypes, E_Compression

if "--hwut-info" in sys.argv:
    print "Paths: collect;"
    print "CHOICES: 1, 2, 3, 4, 5, 6;"#, extreme;"
    sys.exit(0)

def construct_path(sm, StartStateIdx, String, Skeleton):
    state_idx = StartStateIdx
    i = 0
    for letter in String:
        i += 1
        char = int(ord(letter))
        for target_idx, trigger_set in Skeleton.items():
            adapted_trigger_set = trigger_set.difference(NumberSet(char))
            end = sm.add_transition(state_idx, trigger_set, target_idx, True)
            sm.states[end].mark_self_as_origin(target_idx + 1000, end)
        
        state_idx = sm.add_transition(state_idx, char, None, True)
        sm.states[state_idx].mark_self_as_origin((long)(i + 10000), end)

    return state_idx # Return end of the string path

def number_set(IntervalList):
    result = NumberSet(map(lambda x: Interval(x[0], x[1]), IntervalList))
    return result

filter_f = False
def test(Skeleton, *StringPaths):
    global filter_f

    sm = core.StateMachine()

    idx0 = sm.init_state_index
    for character_sequence in StringPaths:
        idx = construct_path(sm, idx0, character_sequence, Skeleton)

    sm = nfa_to_dfa.do(sm)

    # Path analyzis may not consider the init state, so mount 
    # an init state before everything.
    sm.add_transition(7777L, ord('0'), sm.init_state_index)
    sm.init_state_index = 7777L

    sm = sm.normalized_clone()
    print sm.get_graphviz_string(NormalizeF=False)
    print
    analyzer = Analyzer(sm, E_EngineTypes.FORWARD)
    for state in analyzer.state_db.itervalues():
        state.entry.door_tree_configure()
    result = paths.collect(analyzer, 
                           CompressionType=E_Compression.PATH, 
                           AvailableStateIndexList=analyzer.state_db.keys())
    if filter_f:
        result = paths.select(result)

    for path in sorted(result, key=lambda x: (-len(x), x.sequence()[0].state_index)):
        print "# " + path.get_string().replace("\n", "\n# ")

skeleton_blah = { 
   6666666L: NumberSet(Interval(ord('#'))),
}
skeleton_0 = { 
   66L: NumberSet(Interval(ord('a'))),
}
skeleton_1 = { 
   6666L: NumberSet(Interval(ord('a'), ord('z')+1)),
}

skeleton_2 = {} 
for char in "abc":
    letter = ord(char)
    random = (letter % 15) + 1000
    trigger = NumberSet(Interval(letter))
    skeleton_2.setdefault(long(random), NumberSet()).unite_with(NumberSet(int(letter)))

skeleton_3 = {} 
for char in "bc":
    letter = ord(char)
    random = (letter % 15) + 1000
    trigger = NumberSet(Interval(letter))
    skeleton_3.setdefault(long(random), NumberSet()).unite_with(NumberSet(int(letter)))

skeleton_4 = {} 
for char in "cd":
    letter = ord(char)
    random = (letter % 15) + 1000
    # Add intervals that have an extend of '2' so that they do not
    # add possible single paths.
    trigger = NumberSet(Interval((letter % 2) * 2, (letter % 2) * 2 + 2))
    skeleton_4.setdefault(long(random), NumberSet()).unite_with(NumberSet(int(letter)))

# Hint: Use 'dot' (graphviz utility) to print the graphs.
# EXAMPLE:
#          > ./paths-find_paths.py 2 > tmp.dot
#          > dot tmp.dot -Tfig -o tmp.fig       # produce .fig graph file 
#          > xfig tmp.fig                       # use xfig to view
if   len(sys.argv) < 2:
    print "Call this with: --hwut-info"
elif "1" in sys.argv: test(skeleton_2, "cb")
elif "2" in sys.argv: test(skeleton_0, "cc")
elif "3" in sys.argv: test(skeleton_0, "ca")
elif "4" in sys.argv: test(skeleton_3, "ccccb")
elif "5" in sys.argv: test(skeleton_1, "abc", "cde")
elif "6" in sys.argv: test(skeleton_4, "cde")
elif "extreme" in sys.argv: 
    filter_f=True; 
    # test_str = "abcdefghijklmnopqrstuvwxyz" * (- int(sys.argv[2]))
    test_str = "abcdefghijklmnopqrstuvw" * (- int(sys.argv[2]))
    test(skeleton_blah, test_str)
    print "#", test_str

