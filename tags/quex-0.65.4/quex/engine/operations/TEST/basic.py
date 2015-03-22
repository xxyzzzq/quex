#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# Iterating over all existing commands and examining what the commands
# actually do. That is, 
#
#    -- what registers they access. 
#    -- If they acces the registers read or write, 
#    -- if they 'branch', 
#    -- how much the involved computational cost is.
#    -- Their C representation
# 
# If a command from E_Op is not in the example_db, then this test prints
# an error message and quits.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.operations.operation_list         import *
from   quex.engine.operations.operation_list         import _cost_db, \
                                                _brancher_set
from   quex.engine.operations.TEST.helper  import example_db
from   quex.engine.analyzer.door_id_address_label import DoorID
import quex.engine.operations.shared_tail  as     command_list_shared_tail
from   quex.output.core.dictionary       import db

from   quex.blackboard import E_Op, \
                              setup as Setup, \
                              Lng

from   collections import defaultdict
from   copy        import deepcopy

Setup.language_db = db[Setup.language]

if "--hwut-info" in sys.argv:
    print "Command: Basic;"
    sys.exit()


missing_set = set(cmd_id for cmd_id in E_Op if cmd_id != E_Op._DEBUG_Commands)
def test(Op):
    global missing_set
    # safeguard against double occurence
    if Op.id in missing_set: missing_set.remove(Op.id)
    print "%s" % Op.id
    print "   <%s>" % str(Op).replace("\n", "")
    print "   Registers:   ", 
    for register, right in sorted(Op.get_register_access_iterable()):
        txt = ""
        if right.write_f: txt += "w"
        if right.read_f:  txt += "r"
        print "%s(%s), " % (register, txt),
    print
    if Op.id in _brancher_set: 
        print "   IsBranching: True"
    print "   Cost:        ", _cost_db[Op.id]
    print "   C-code: {"
    for line in Lng.COMMAND(Op).splitlines():
        print "       %s" % line
    print "   }\n"


for cmd_id in sorted(E_Op, key=lambda x: "%s" % x):
    if cmd_id == E_Op._DEBUG_Commands: 
        continue
    elif cmd_id not in example_db:
        sys.exit()
    for cmd in example_db[cmd_id]:
        test(cmd)

