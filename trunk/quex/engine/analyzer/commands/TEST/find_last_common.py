#! /usr/bin/env python
# -*- coding: utf8 -*-
# 
# 'find_last_common(A, B)' searches for the last command in A and B which 
# they have in common. For that the '==' (compare equal) operator must work
# properly. 
#
# EqualOp: The first choice checks that the available commands are compared
#          correctly. 
#
# normal:  Runs test with the function 'find_last_common'.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

import os 
import sys 
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.blackboard                            import E_Cmd
from   quex.engine.analyzer.commands.core         import *
from   quex.engine.analyzer.commands.shared_tail  import find_last_common
from   quex.engine.analyzer.commands.TEST.helper  import example_db
from   quex.engine.analyzer.door_id_address_label import DoorID

from   collections import defaultdict
from   itertools   import izip, permutations
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "Command.shared_tail: find_last_common;"
    print "CHOICES: EqualOp, no-common, 1-common, 2-common, 3-common, start-indices;"
    sys.exit()

def generator():
    """Iterable over all commands from the example_db.
    """
    index = 0
    for example_list in example_db.itervalues():
        for example in example_list:
            index += 1
            yield index, example

shared_list     = []
non_shared_list = []
non_shared_i    = 0
shared_i        = 0
def setup():
    global shared_list
    global non_shared_list
    global non_shared_i

    del shared_list[:]
    del non_shared_list[:]
    non_shared_i = 0

    selectable = generator()

    # 1st five --> The shared commands.
    for i, cmd in selectable:
        if i > 5: break
        shared_list.append(cmd)

    # Remaining --> The non-shared commands.
    non_shared_list.append(cmd)
    for i, cmd in selectable:
        non_shared_list.append(cmd)

    shared_i = 0

def get(Flag):
    global shared_i 
    global non_shared_i 
    if Flag != 0: 
        result    = shared_list[shared_i-1]
        shared_i += 1 
    else:    
        result        = non_shared_list[non_shared_i]
        non_shared_i += 1
    return result

def print_cl(Name, Cl):
    if len(Cl) == 0:
        print "    %s: <empty>" % Name
        return
    print "    %s: [0] %s" % (Name, Cl[0])
    for i, cmd in enumerate(Cl[1:]):
        print "       [%i] %s" % (i+1, cmd)

def test(CmdN0, CmdN1, CommonN=0):
    global shared_i
    print
    print "[L1=%i; L2=%i; Common=%i]" % (CmdN0, CmdN1, CommonN)
    if CommonN == 0:
        setup()
        cl0 = [ get(0) for i in xrange(CmdN0) ]
        cl1 = [ get(0) for i in xrange(CmdN1) ]
        print_cl("A", cl0)
        print_cl("B", cl1)
        print "    last common at: %s" % str(find_last_common(cl0, cl1, len(cl0)-1, len(cl1)-1))
        print
    else:
        info0 = [0] * (CmdN0 - CommonN) + [1] * CommonN
        info1 = [0] * (CmdN1 - CommonN) + [1] * CommonN
        for selection0 in set(permutations(info0)):
            for selection1 in set(permutations(info1)):
                setup()
                shared_i = 0
                cl0 = [ get(flag) for flag in selection0 ]
                shared_i = 0
                cl1 = [ get(flag) for flag in selection1 ]
                print_cl("A", cl0)
                print_cl("B", cl1)
                print "    last common at: %s" % str(find_last_common(cl0, cl1, len(cl0)-1, len(cl1)-1))
                print

if "EqualOp" in sys.argv:
    # No two commands from the example db are the same. The equal operator
    # should fail on all possible combinations.
    eq_n  = 0
    neq_n = 0
    for i, cmd_i in generator():
        for k, cmd_k in generator():
            if i == k: 
                eq_n += 1
                assert     (cmd_i == cmd_k) and not (cmd_i != cmd_k)
            else:      
                neq_n += 1 
                assert not (cmd_i == cmd_k) and     (cmd_i != cmd_k)

    L = len([x for x in generator()])
    print "Equal number: %i/%i; not equal: %i/%i" % (eq_n, L, neq_n, (L*(L-1)))
    print "Oll Korrekt:" # Otherwise the 'assert'-s would have kicked us out!

elif "no-common" in sys.argv:
    print "(1)   One empty __________________________________________________"
    test(0, 0)
    test(0, 1)
    test(0, 2)
    test(0, 3)
    print "(2)   One with 1 element _________________________________________"
    test(1, 1)
    test(1, 2)
    test(1, 3)
    print "(3)   One with 2 elements ________________________________________"
    test(2, 2)
    test(2, 3)
    print "(4)   One with 3 elements ________________________________________"
    test(3, 3)

elif "1-common" in sys.argv:
    print "(1)   One with 1 element _________________________________________"
    test(1, 1, 1)
    test(1, 2, 1)
    test(1, 3, 1)
    print "(2)   One with 2 elements ________________________________________"
    test(2, 2, 1)
    test(2, 3, 1)
    print "(3)   One with 3 elements ________________________________________"
    test(2, 3, 1)

elif "2-common" in sys.argv:
    print "(1)   One with 2 elements ________________________________________"
    test(2, 2, 2)
    test(2, 3, 2)
    print "(2)   One with 3 elements ________________________________________"
    test(3, 3, 2)

elif "3-common" in sys.argv:
    print "(1)   One with 3 elements ________________________________________"
    test(3, 3, 3)
    test(3, 4, 3)
    test(3, 5, 3)

elif "start-indices":
    #              0  1  2  3  4  5  6  7  8  9 10 11
    selection0 = [ 0, 0, 1, 0, 2, 3, 4, 0, 0, 0, 5, 0]
    selection1 = [ 1, 0, 2, 3, 0, 0, 0, 0, 4, 0, 0, 5]

    # db[x] = y means: last command at position 'x' was 'y' 
    last0_db   = [-1,-1, 1, 1, 2, 3, 4, 4, 4, 4, 5, 5 ]
    last1_db   = [ 1, 1, 2, 3, 3, 3, 3, 3, 4, 4, 4, 5 ]
    setup()
    shared_i = 0
    cl0 = [ get(flag) for flag in selection0 ]
    shared_i = 0
    cl1 = [ get(flag) for flag in selection1 ]

    count_i = 0
    for i in xrange(len(selection0)-1, -1, -1):
        for k in xrange(len(selection1)-1, -1, -1):
            count_i += 1
            last_i, last_k = find_last_common(cl0, cl1, i, k)
            # print_cl("cl0", cl0)
            # print_cl("cl1", cl1)
            last_common = min(last0_db[i], last1_db[k])
            if last_common == -1:
                assert last_i is None and last_k is None
            else:
                expected_last_i = selection0.index(last_common)
                expected_last_k = selection1.index(last_common)
                assert last_i == expected_last_i, "i: %i; last common: %i; expected: %i;" % (i, last_i, expected_last_i)
                assert last_k == expected_last_k, "i: %i; last common: %i; expected: %i;" % (k, last_k, expected_last_k)

    print "%i Oll Korrekt!" % count_i # Otherwise, asserts would have thrown us out!

