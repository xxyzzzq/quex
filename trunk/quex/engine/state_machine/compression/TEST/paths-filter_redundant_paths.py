#! /usr/bin/env python
import sys
import os
from   copy import deepcopy
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.engine.interval_handling import *
from quex.engine.state_machine.compression.paths import __filter_redundant_paths, CharacterPath

if "--hwut-info" in sys.argv:
    print "Paths: filter_redundant_paths;"
    print "CHOICES: 0, 1, 2, 3 , 4, 5a, 5b, 6;"
    sys.exit(0)
    

def get_path_list(PlainLists):
    dummy_char = ord("a")
    result = []
    for sequence in PlainLists:
        path = CharacterPath(sequence[0], {}, dummy_char)
        for state_index in sequence[1:-1]:
            path.append(state_index, dummy_char) 
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
