#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.paths as paths 

if "--hwut-info" in sys.argv:
    print "Paths: extract_admissible_single_transitions;\n"
    print "CHOICES: single, more;"
    sys.exit(0)
    
def number_set(IntervalList):
    result = NumberSet(map(lambda x: Interval(x[0], x[1]), IntervalList))
    return result

def get_map(*TriggerSetList):
    db = {}
    for item in TriggerSetList:
        target_idx  = item[0]
        trigger_set = item[1:]
        db[target_idx] = number_set(trigger_set)
    return db

def test(A, B):
    print "A", A
    print "B", B
    print paths.extract_admissible_single_transitions(B, A)
    print paths.extract_admissible_single_transitions(A, B)


if "single" in sys.argv:
    A = get_map([0, [1, 2]])
    B = get_map([0, [1, 2]])
    test(A, B)

    A = get_map([0, [2, 3]])
    B = get_map([0, [1, 2]])
    test(A, B)

    A = get_map([1, [1, 2]])
    B = get_map([0, [1, 2]])
    test(A, B)

    A = get_map([1, [2, 3]])
    B = get_map([0, [1, 2]])
    test(A, B)

else:
    A = get_map([1, [2, 3]], [2, [4, 5]])
    B = get_map([0, [1, 2]])
    test(A, B)

    A = get_map([1, [2, 3]], [2, [4, 5]])
    B = get_map([2, [1, 2]], [0, [4, 5]])
    test(A, B)

# A = get_map([0, [0, 1]], [1, [1, 2]], [2, [3, 4]])
# B = get_map([0, [0, 1]], [1, [1, 2]], [2, [3, 4]])

