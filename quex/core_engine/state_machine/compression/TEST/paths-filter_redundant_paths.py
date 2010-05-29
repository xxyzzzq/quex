#! /usr/bin/env python
import sys
import os
from   copy import deepcopy
sys.path.insert(0, os.environ["QUEX_PATH"])


from quex.core_engine.interval_handling import *
from quex.core_engine.state_machine.compression.paths import __filter_redundant_paths, CharacterPath

if "--hwut-info" in sys.argv:
    print "Paths: filter_redundant_paths;"
    print "CHOICES: 0, 1;"
    sys.exit(0)
    

def get_path_list(PlainLists):
    result = []
    for sequence in PlainLists:
        path = CharacterPath(sequence[0], {}, None)
        for state_index in sequence[1:-1]:
            path.append(state_index, 1)     # any character works, choose '1'
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
