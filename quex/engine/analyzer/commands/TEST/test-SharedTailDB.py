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
from   quex.engine.analyzer.commands.tree         import SharedTailDB
from   quex.engine.analyzer.commands.TEST.helper  import *
from   quex.engine.analyzer.door_id_address_label import DoorID, dial_db

from   collections import defaultdict
from   itertools   import izip, permutations
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "SharedTailDB;"
    print "CHOICES: init, pop_best, _find_best, _remove, _new_node, _enter;"
    sys.exit()

alias_db = dict(
    (cmd, "c%X" % i) for i, cmd in generator()
)

def test_init(DidCl_Iterable):
    dial_db.clear()
    stdb = SharedTailDB(4711, DidCl_Iterable)

    print "_" * 80
    print "SharedTailDB:" 
    print
    print "    " + stdb.get_string(alias_db).replace("\n", "\n    ")

test_init([])
test_init([(DoorID(0, 1), [generator().next()])])
