#! /usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.analyzer.commands.core import *
from   quex.engine.analyzer.commands.core import _cost_db
from   quex.engine.analyzer.door_id_address_label   import DoorID
import quex.engine.analyzer.commands.shared_tail as command_list_shared_tail
from   quex.engine.generator.languages.core        import db

from   quex.blackboard               import E_Cmd, \
                                            setup as Setup, \
                                            Lng

from   collections import defaultdict
from   copy import deepcopy

Setup.language_db = db[Setup.language]

if "--hwut-info" in sys.argv:
    print "CommandList: Basic;"
    print "CHOICES:     2-1, no-common, all-common, misc;"
    sys.exit()


missing_set = set(cmd_id for cmd_id in E_Cmd if cmd_id != E_Cmd._DEBUG_Commands)
def test(Cmd):
    global missing_set
    # safeguard against double occurence
    if Cmd.id in missing_set: missing_set.remove(Cmd.id)
    print "Command:      %s" % Cmd.id
    print "   Registers:   ", 
    for register, right in sorted(get_register_access_db(Cmd).items()):
        txt = ""
        if right.write_f: txt += "w"
        if right.read_f:  txt += "r"
        print "%s(%s), " % (register, txt),
    print
    print "   IsBranching: ", is_branching(Cmd.id)
    print "   Cost:        ", _cost_db[Cmd.id]
    print "   C-code: {"
    for line in Lng.COMMAND(Cmd).split("\n"):
        print "    %s" % line
    print "   }\n"

def after_math():
    # Check that every command has been checked
    global missing_set
    if len(missing_set) == 0:
        print "[OK] All command have been checked"
        return 

    for cmd_id in missing_set:
        print "Missing: %s -- no test implemented" % cmd_id

test(StoreInputPosition(4711, 7777, 0))
test(StoreInputPosition(4711, 7777, 1000))
test(PreContextOK(4711))
test(TemplateStateKeySet(66))
test(PathIteratorSet(11, 22, 1000))
test(PrepareAfterReload(DoorID(33, 44), DoorID(55, 66)))
test(InputPIncrement())
test(InputPDecrement())
test(InputPDereference())
test(LexemeResetTerminatingZero())
test(ColumnCountReferencePSet(E_R.CharacterBeginP, 1000))
test(ColumnCountReferencePDeltaAdd(E_R.CharacterBeginP, 5555))
test(ColumnCountAdd(1))
test(ColumnCountGridAdd(4))
test(ColumnCountGridAddWithReferenceP(1, E_R.CharacterBeginP, 5555))
test(LineCountAdd(1))
test(LineCountAddWithReferenceP(1, E_R.CharacterBeginP, 5555))
test(GotoDoorId(DoorID(33,44)))
test(GotoDoorIdIfInputPNotEqualPointer(DoorID(33,44), E_R.CharacterBeginP))
test(Assign(E_R.InputP, E_R.LexemeStartP))
test(Accepter())

after_math()
