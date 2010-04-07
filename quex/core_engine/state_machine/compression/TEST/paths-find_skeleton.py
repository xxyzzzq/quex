#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.core_engine.interval_handling import *
import quex.core_engine.state_machine.compression.paths as paths 

if "--hwut-info" in sys.argv:
    print "Paths: find_skeleton;"
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

def print_map(Map):
    add_info = ""
    if Map == None: 
        print "  None"; return
    elif type(Map) == tuple:
        add_info  = "  1st: [%i] -> %i;" % (Map[1][1], Map[1][0])
        add_info += " 2nd: [%i] -> %i\n" % (Map[2][1], Map[2][0])
        Map = Map[0]

    trigger_map = []
    for target_idx, trigger_set in Map.items():
        interval_list = trigger_set.get_intervals()
        new_info_list = map(lambda x: (x.begin, x.end - 1, target_idx),
                            interval_list)
        trigger_map.extend(new_info_list)
    trigger_map.sort()

    if trigger_map == []:
        print "  <empty map>"

    for info in trigger_map:
        if info[1] - info[0] != 0: interval_str = "[%i-%i]" % (info[0], info[1])
        else:                      interval_str = "[%i]   " % info[0]
        print "  " + interval_str + (" " * (8-len(interval_str))) + "-> %i" % info[2]

    if add_info != "":
        print add_info

def test(A, B):
    print "A:"
    print_map(A)
    print "B:"
    print_map(B)
    print "Skeleton from (A,B):"
    print_map(paths.find_skeleton(A, B))
    print "Skeleton from (B,A):"
    print_map(paths.find_skeleton(B, A))
    print "-" * 70

if "single" in sys.argv:
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
    B = get_map([0, [1, 2]], [2, [4, 5]])
    test(A, B)

    A = get_map([1, [1, 3]],              [3, [5, 6]], [5, [6, 10]])
    B = get_map([1, [1, 2]], [2, [2, 3]],              [5, [5, 10]])
    test(A, B)

    A = get_map([1, [1, 3]],              [5, [5, 10]])
    B = get_map([1, [1, 2]], [2, [2, 3]], [5, [5, 10]])
    test(A, B)

    A = get_map([1, [1, 6], [7,10]], [2, [6, 7]])
    B = get_map([1, [1, 3], [4,10]], [3, [3, 4]])
    test(A, B)

    A = get_map([555, [2, 3]], [110, [3, 4]])
    B = get_map([120, [2, 3]], [666, [3, 4]])
    # A = get_map([100, [1, 2]], [550, [2, 3]], [130, [3, 4]], [140, [4, 5]])
    # B = get_map([100, [1, 2]], [110, [2, 3]], [660, [3, 4]], [140, [4, 5]])
    test(A, B)

