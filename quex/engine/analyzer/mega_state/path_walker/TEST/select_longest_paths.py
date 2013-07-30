#! /usr/bin/env python
import sys
import os
from   copy import deepcopy
sys.path.insert(0, os.environ["QUEX_PATH"])


from   quex.engine.interval_handling    import *
import quex.engine.state_machine.core   as     core
from   quex.engine.analyzer.state.core  import AnalyzerState
from   quex.engine.analyzer.mega_state.path_walker.core   import select, CharacterPath     
from   quex.engine.analyzer.transition_map                import TransitionMap              
import quex.engine.analyzer.engine_supply_factory      as     engine

if "--hwut-info" in sys.argv:
    print "Paths: select;"
    print "CHOICES: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11a, 11b, 12;"
    sys.exit(0)
    

def get_analyzer_state(sm, state_index):
    sm.states[state_index] = core.State()
    state = AnalyzerState(sm.states[state_index], state_index, state_index == sm.init_state_index, engine.FORWARD, set()) 
    state.entry.action_db.categorize()
    return state

def get_path_list(PlainLists):
    dummy_char = ord("a")
    dummy_sm   = core.StateMachine()

    result = []
    for sequence in PlainLists:
        path = CharacterPath(get_analyzer_state(dummy_sm, sequence[0]), dummy_char, 
                             TransitionMap.from_iterable([(Interval(-sys.maxint, sys.maxint), "1")]))
        for state_index in sequence[1:-1]:
            path.append_state(get_analyzer_state(dummy_sm, state_index), dummy_char)

        path.append_state(get_analyzer_state(dummy_sm, sequence[-1]))
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
        print "  ", i, map(lambda x: x.state_index, path.step_list[:-1])

    path_list = select(path_list)

    print "AFTER:"
    for i, path in enumerate(path_list):
        print "  ", i, map(lambda x: x.state_index, path.step_list[:-1])
    print


if "0" in sys.argv:
    test([1L, 2L, 3L],
         [4L, 2L, 3L])

elif "1" in sys.argv:
    test([1L, 2L, 3L],
         [6L, 2L, 4L, 5L])

elif "2" in sys.argv:
    print "## End states may appear in other paths without contradiction."
    test([1L, 2L, 4L],
         [3L, 4L, 5L, 6L])

elif "3" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L],
         [2L, 3L, 4L])

elif "4" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L, 4L, 5L],
         [2L, 3L, 4L],
         [1L, 2L])

elif "5" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 4L])

elif "6" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L])
elif "7" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L])
elif "8" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L],
         [2L, 3L])
elif "9" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L, 3L])
elif "10" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L, 4L])
elif "11a" in sys.argv:
    test([1L, 2L, 3L],
         [1L, 2L],
         [2L, 3L, 4L])
elif "11b" in sys.argv:
    test([1L, 2L, 3L],
         [2L, 3L, 4L],
         [1L, 2L])
elif "12" in sys.argv:
    test([1L, 2L, 3L, 4L],
         [2L, 3L])
