#! /usr/bin/env python
# -*- coding: utf8 -*-
# 
# 'shared_tail.get(A, B)' identifies commands from A and B which can be
# combined into an appended shared tail. 
#
# The main part of the function is done in 'can_be_moved_to_tail()' and
# 'find_last_common()'. Those two functions are tested in dedicated tests.
#
#  => No need to test:
#       if the last common is found correctly.
#       if the command is judged as being moveable to the tail.
#
#  => Test, if the tail is extracted correctly, that is:
#       All tail-commands: (1) appear in the tail,
#                          (2) in their propper sequence.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

import os 
import sys 
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.blackboard                            import E_Cmd
from   quex.engine.analyzer.commands.core         import *
import quex.engine.analyzer.commands.shared_tail  as     shared_tail
from   quex.engine.analyzer.commands.TEST.helper  import *
from   quex.engine.analyzer.door_id_address_label import DoorID

from   collections import defaultdict
from   itertools   import izip, permutations
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "Command.shared_tail: find_last_common;"
    print "CHOICES: one-or-none;"
    sys.exit()

A = Assign(E_R.CharacterBeginP, E_R.Input)
B = Assign(E_R.CharacterBeginP, E_R.LexemeEnd)
C = Assign(E_R.CharacterBeginP, E_R.Line)

x = [ remaining for i, remaining in generator() if remaining not in (A, B, C) ]

def print_tail_vs_cmd_list(Tail, CmdList, P):
    t = 0
    for i, cmd in enumerate(CmdList):
        if t < len(Tail) and Tail[t][P] == i: label = "<%i>" % t; t += 1
        else:                                 label = "   "
        print "   %s %s" % (label, str(cmd))

def test(Cl0, Cl1):
    tail = shared_tail.get(Cl0, Cl1)
    if tail is None: tail = []
    itail = shared_tail.get(Cl1, Cl0)
    if itail is None: itail = []

    print
    print "_" * 80
    print "tail(A, B): {"
    print_tail_vs_cmd_list(tail, Cl0, 0)
    print "   - - - - - - "
    print_tail_vs_cmd_list(tail, Cl1, 1)
    print "}"

    print "tail(B, A): {"
    count_n = 0
    for x, y in izip(tail, itail):
        i0, k0 = x
        i1, k1 = y
        if i1 != k0 or k1 != i0:
            # Print error case
            print_tail_vs_cmd_list(itail, Cl0, 1)
            print "   - - - - - - "
            print_tail_vs_cmd_list(itail, Cl1, 0)
        assert i1 == k0
        assert k1 == i0
        count_n += 1

    print "    %s x same" % count_n
    print "}"

if False:
    test([], [])
    test([ A ], [])
    test([ A ], [ A ])
    test([ A ], [ B ])
    test([ A ], [ x[0], x[1] ])
    test([ A ], [ x[0], A, x[1] ])
    test([ A ], [ x[0], B, x[1] ])
    test([ x[2], A, x[3] ], [ x[0], x[1] ])
test([ x[2], A, x[3] ], [ x[0], A, x[1] ])
if False:
    test([ x[2], A, x[3] ], [ x[0], B, x[1] ])
# test([ A, x[0], A, B ], [ x[1], A, B ])

