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
from   quex.engine.commands.core         import *
import quex.engine.commands.shared_tail  as     shared_tail
from   quex.engine.commands.tree         import SharedTailDB
from   quex.engine.commands.TEST.helper  import *
from   quex.engine.analyzer.door_id_address_label import DoorID, dial_db

from   collections import defaultdict
from   itertools   import izip, permutations
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "SharedTailDB;"
    print "CHOICES: init, pop_best;"
    sys.exit()

# Generate a set of totally independent commands
# Here, they are assigned manually, to avoid that changes to E_R might
# might produce commands that block the 'move to tail'.
A = Command.Assign(E_R.AcceptanceRegister, E_R.Buffer)
B = Command.Assign(E_R.Indentation, E_R.Column)
C = Command.Assign(E_R.Input, E_R.InputP)
D = Command.Assign(E_R.LexemeStartP, E_R.LexemeEnd)
E = Command.Assign(E_R.CharacterBeginP, E_R.Line)
F = Command.Assign(E_R.PathIterator, E_R.PreContextFlags)
G = Command.Assign(E_R.ReferenceP, E_R.PositionRegister)

alias_db = { A: "A", B: "B", C: "C", D: "D", E: "E", F: "F", G: "G", }

def test_init(DidCl_Iterable):
    dial_db.clear()
    stdb = SharedTailDB(4711L, DidCl_Iterable)

    print "_" * 80
    print
    print "Setup:"
    for door_id, command_list in DidCl_Iterable:
         print "    %s: [%s]" % (str(door_id), ("".join("%s " % alias_db[cmd] for cmd in command_list)).strip())
    print
    print "SharedTailDB:" 
    print
    print "    " + stdb.get_string(alias_db).replace("\n", "\n    ")

def test_pop(DidCl_Iterable):
    dial_db.clear()
    stdb = SharedTailDB(4711L, DidCl_Iterable)

    print "_" * 80
    print
    print "Setup:"
    for door_id, command_list in DidCl_Iterable:
        print "    %s: [%s]" % (str(door_id), ("".join("%s " % alias_db[cmd] for cmd in command_list)).strip())

    print
    print "___ Initial ___"
    print
    print "".join(stdb.get_tree_text(alias_db))

    i = 0
    while stdb.pop_best():
        i += 1
        print "___ Step %i ____" % i
        print
        print "".join(stdb.get_tree_text(alias_db))

        
setup_list = [
    [],
    [
        (DoorID(0, 1), [A]),
    ],
    [
        (DoorID(0, 1), [A]), 
        (DoorID(0, 2), [A]),
    ],
    [
        (DoorID(0, 1), [A]), 
        (DoorID(0, 2), [B]),
    ],
    [
        (DoorID(0, 1), [A, C]), 
        (DoorID(0, 2), [A, C]),
    ],
    [
        (DoorID(0, 1), [A, C]), 
        (DoorID(0, 2), [B, C]),
    ],
    [
        (DoorID(0, 1), [C, A]), 
        (DoorID(0, 2), [C, B]),
    ],
    [
        (DoorID(0, 1), [A, C]), 
        (DoorID(0, 2), [C, B]),
    ],
    [
        (DoorID(0, 1), [A, C]), 
        (DoorID(0, 2), [C, A]),
    ],
    [
        (DoorID(0, 1), [A, C]), 
        (DoorID(0, 2), [B, C]),
        (DoorID(0, 3), [D, C]), 
        (DoorID(0, 4), [E, C]),
    ],
    [
        (DoorID(0, 1), [A, C, F]), 
        (DoorID(0, 2), [B, C, F]),
        (DoorID(0, 3), [D, G, F]), 
        (DoorID(0, 4), [E, G, F]),
    ],
    [
        (DoorID(0, 1), [A, C, F]), 
        (DoorID(0, 2), [B, F, C]),
        (DoorID(0, 3), [F, D, G]), 
        (DoorID(0, 4), [G, F, E]),
    ],
]

if "init" in sys.argv:
    # test_init(setup_list[8])
    for door_id_command_list in setup_list:
        test_init(door_id_command_list)

elif "pop_best" in sys.argv:
    for door_id_command_list in setup_list:
         test_pop(door_id_command_list)

elif "large_init" in sys.argv:
    door_id_command_list = []
    for i in xrange(200):
        door_id      = DoorID(0, i)
        command_list = random_command_list(5, Seed=0)
        door_id_command_list.append((door_id, command_list))
    test_init(door_id_command_list)
