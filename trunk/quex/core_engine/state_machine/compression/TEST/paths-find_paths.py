#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.core                  as core
import quex.core_engine.state_machine.nfa_to_dfa            as nfa_to_dfa
import quex.core_engine.state_machine.hopcroft_minimization as hopcroft
import quex.core_engine.state_machine.compression.paths     as paths 

if "--hwut-info" in sys.argv:
    print "Paths: find_path;"
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
        sm.states[state_idx].mark_self_as_origin(i + 10000, end)

    return state_idx # Return end of the string path

def number_set(IntervalList):
    result = NumberSet(map(lambda x: Interval(x[0], x[1]), IntervalList))
    return result

def test(Skeleton, *StringPaths):
    sm = core.StateMachine()

    # def construct_path(sm, StartStateIdx, String, Skeleton):
    idx0 = sm.init_state_index
    for character_sequence in StringPaths:
        idx = construct_path(sm, idx0, character_sequence, Skeleton)

    sm = nfa_to_dfa.do(sm)
    sm = hopcroft.do(sm)

    # print Skeleton
    print sm.get_graphviz_string(NormalizeF=False)
    print
    result = paths.find_paths(sm)
    for path in result:
        print "# " + repr(path).replace("\n", "\n# ")

skeleton_1 = { 
   6666L: NumberSet(Interval(ord('a'), ord('z')+1)),
}

skeleton_2 = {} 
for letter in range(ord("a"), ord("e") + 1) + range(ord("A"), ord("Z") + 1):
    random = (letter % 15) + 1000
    # Add intervals that have an extend of '2' so that they do not
    # add possible single paths.
    trigger = NumberSet(Interval((letter % 2) * 2, (letter % 2) * 2 + 2))
    skeleton_2.setdefault(long(random), NumberSet()).unite_with(NumberSet(int(letter)))

if   "1" in sys.argv: test(skeleton_1, "ab", "cde")
elif "2" in sys.argv: test(skeleton_2, "cde")

