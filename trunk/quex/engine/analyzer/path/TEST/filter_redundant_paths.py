#! /usr/bin/env python
import sys
import os
from   copy import deepcopy
sys.path.insert(0, os.environ["QUEX_PATH"])


import quex.engine.state_machine.core  as     core
from   quex.engine.analyzer.state.core import AnalyzerState
from   quex.engine.analyzer.path.core  import __filter_redundant_paths, CharacterPath     
from   quex.blackboard                 import E_EngineTypes
from   quex.engine.interval_handling   import *

if "--hwut-info" in sys.argv:
    print "Paths: filter_redundant_paths;"
    print "CHOICES: 0, 1, 2, 3 , 4, 5a, 5b, 6;"
    sys.exit(0)
    

def get_analyzer_state(sm, state_index):
    sm.states[state_index] = core.State()
    state = AnalyzerState(sm.states[state_index], state_index, state_index == sm.init_state_index, E_EngineTypes.FORWARD, set()) 
    state.entry.door_tree_configure()
    return state

def get_path_list(PlainLists):
    dummy_char = ord("a")
    dummy_sm   = core.StateMachine()

    result = []
    for sequence in PlainLists:
        path = CharacterPath(get_analyzer_state(dummy_sm, sequence[0]), dummy_char, {})
        for state_index in sequence[1:-1]:
            path.append(get_analyzer_state(dummy_sm, state_index), dummy_char) 

        path.set_end_state_index(sequence[-1])
        result.append(path)
    return result

def test(*PlainLists):
    path_list = get_path_list(PlainLists)
    print "_________________________________________________________"
    backup = deepcopy(path_list)
    __test(path_list)
    print "REVERSE__________________________________________________"
    backup.reverse()
    __test(backup)

def __test(path_list):
    print
    print "BEFORE:"
    for i, path in enumerate(path_list):
        print "  ", i, map(lambda x: x[0], path.sequence())

    __filter_redundant_paths(path_list)

    print "AFTER:"
    for i, path in enumerate(path_list):
        print "  ", i, map(lambda x: x[0], path.sequence())
    print



if "0" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L])
elif "1" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L])
elif "2" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L],
         [2L, 3L])
elif "3" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L, 3L])
elif "4" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L, 4L])
elif "5a" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L],
         [2L, 3L, 4L])
elif "5b" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L, 4L],
         [1L, 2L])
elif "6" in sys.argv:
    test([1L, 2L, 3L, 4L],
         [2L, 3L])
