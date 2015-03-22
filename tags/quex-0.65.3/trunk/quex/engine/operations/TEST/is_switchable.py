#! /usr/bin/env python
# -*- coding: utf8 -*-
# 
# Function 'commands.is_switchable(A, B)' checks whether two commands can be
# switched in a sequence of commands. This is not possible, in particular, if
# one of the commands is a 'brancher' (i.e. jumps) or if they read/write to the
# same register.
# 
# It DOES NOT iterate over all commands. What commands are supposed to do is
# tested in 'basic.py'
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

import os 
import sys 
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.blackboard                            import E_Op
from   quex.engine.operations.operation_list         import *
from   quex.engine.operations.TEST.helper  import example_db
from   quex.engine.analyzer.door_id_address_label import DoorID

from   collections import defaultdict
from   itertools   import islice
from   copy        import deepcopy

if "--hwut-info" in sys.argv:
    print "Op: is_switchable;"
    sys.exit()


def test(A, B):
    print "   A: %s" % str(A).replace("\n", "")
    print "   B: %s" % str(B).replace("\n", "")
    assert is_switchable(A, B) == is_switchable(B, A)
    print
    print "   is_switchable: ", is_switchable(A, B)
    print

print "(1) Non-branchers: ___________________________________________________________"
print
print "(1.1) Commands with no interferring access to registers ______________________"
print
test(Op.StoreInputPosition(0, 0, 0), 
     Op.StoreInputPosition(0, 1, 0))
test(Op.Assign(E_R.InputP, E_R.CharacterBeginP), 
     Op.Assign(E_R.LexemeStartP, E_R.ReferenceP))
test(Op.ColumnCountAdd(2), 
     Op.LineCountAdd(3))
print "(1.2) Commands with interferring access to registers, solely read ____________"
print
test(Op.InputPDereference(), 
     Op.StoreInputPosition(0, 1, 0))
test(Op.Assign(E_R.InputP,       E_R.ReferenceP), 
     Op.Assign(E_R.LexemeStartP, E_R.ReferenceP))
test(Op.ColumnCountReferencePDeltaAdd(E_R.InputP, 5, False), 
     Op.Assign(E_R.CharacterBeginP, E_R.ReferenceP))
print "(1.3) Commands with interferring access to registers, one read other write ___"
print
test(Op.Assign(E_R.InputP, E_R.CharacterBeginP),    
     Op.StoreInputPosition(0, 1, 0))                
test(Op.Assign(E_R.InputP,       E_R.ReferenceP), 
     Op.Assign(E_R.LexemeStartP, E_R.InputP))
test(Op.ColumnCountReferencePDeltaAdd(E_R.ReferenceP, 5, False), 
     Op.Assign(E_R.ReferenceP, E_R.InputP))
print "(1.4) Commands with interferring access to registers, both write _____________"
print
test(Op.StoreInputPosition(0, 1, 0),
     Op.StoreInputPosition(0, 1, 0))                
test(Op.Assign(E_R.InputP, E_R.ReferenceP), 
     Op.Assign(E_R.InputP, E_R.InputP))
test(Op.ColumnCountReferencePDeltaAdd(E_R.ReferenceP, 5, False), 
     Op.ColumnCountAdd(2))
print "(2) Branchers: _______________________________________________________________"
print
test(Op.GotoDoorId(DoorID(2,2)),
     Op.GotoDoorIdIfInputPNotEqualPointer(DoorID(1,1), E_R.ReferenceP))                
test(Op.GotoDoorId(DoorID(2,2)),
     Op.GotoDoorId(DoorID(1,1)))                
test(Op.GotoDoorIdIfInputPNotEqualPointer(DoorID(2,2), E_R.ReferenceP),               
     Op.GotoDoorIdIfInputPNotEqualPointer(DoorID(1,1), E_R.ReferenceP))                

