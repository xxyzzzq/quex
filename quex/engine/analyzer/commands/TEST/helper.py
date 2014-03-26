from   quex.engine.analyzer.commands.core         import *
from   quex.engine.analyzer.commands.core         import _cost_db
from   quex.engine.analyzer.door_id_address_label import DoorID
import quex.engine.analyzer.commands.shared_tail  as command_list_shared_tail
from   quex.engine.generator.languages.core       import db

from   quex.blackboard import E_Cmd, \
                              setup as Setup, \
                              Lng

from   itertools   import permutations
from   collections import defaultdict
from   copy        import deepcopy


example_db = {
    E_Cmd.StoreInputPosition: [ 
        StoreInputPosition(4711, 7777, 0),
        StoreInputPosition(4711, 7777, 1000) 
    ],
    E_Cmd.PreContextOK:                     [ PreContextOK(4711) ],
    E_Cmd.TemplateStateKeySet:              [ TemplateStateKeySet(66) ],
    E_Cmd.PathIteratorSet:                  [ PathIteratorSet(11, 22, 1000) ],
    E_Cmd.PrepareAfterReload:               [ PrepareAfterReload(DoorID(33, 44), DoorID(55, 66)) ],
    E_Cmd.InputPIncrement:                  [ InputPIncrement() ],
    E_Cmd.InputPDecrement:                  [ InputPDecrement() ],
    E_Cmd.InputPDereference:                [ InputPDereference() ],
    E_Cmd.LexemeResetTerminatingZero:       [ LexemeResetTerminatingZero() ],
    E_Cmd.ColumnCountReferencePSet:         [ ColumnCountReferencePSet(E_R.CharacterBeginP, 1000) ],
    E_Cmd.ColumnCountReferencePDeltaAdd:    [ ColumnCountReferencePDeltaAdd(E_R.CharacterBeginP, 5555) ],
    E_Cmd.ColumnCountAdd:                   [ ColumnCountAdd(1) ],
    E_Cmd.ColumnCountGridAdd: [ 
        ColumnCountGridAdd(1),
        ColumnCountGridAdd(2),
        ColumnCountGridAdd(3),
        ColumnCountGridAdd(4),
        ColumnCountGridAdd(5),
    ],
    E_Cmd.ColumnCountGridAddWithReferenceP: [ 
        ColumnCountGridAddWithReferenceP(1, E_R.CharacterBeginP, 5551),
        ColumnCountGridAddWithReferenceP(2, E_R.CharacterBeginP, 5552),
        ColumnCountGridAddWithReferenceP(3, E_R.CharacterBeginP, 5553),
        ColumnCountGridAddWithReferenceP(4, E_R.CharacterBeginP, 5554),
        ColumnCountGridAddWithReferenceP(5, E_R.CharacterBeginP, 5555),
    ],
    E_Cmd.LineCountAdd: [ LineCountAdd(1) ],
    ## The column number is set to 1 at the newline.
    ## So, no the delta add 'column += (p - reference_p) * c' is not necessary.
    E_Cmd.LineCountAddWithReferenceP:        [ LineCountAddWithReferenceP(1, E_R.CharacterBeginP, 5555) ],
    E_Cmd.GotoDoorId:                        [ GotoDoorId(DoorID(33,44)) ],
    E_Cmd.GotoDoorIdIfInputPNotEqualPointer: [ GotoDoorIdIfInputPNotEqualPointer(DoorID(33,44), E_R.CharacterBeginP) ],
    E_Cmd.Assign:                            [ Assign(E_R.InputP, E_R.LexemeStartP) ],
}

accepter_list = []
accepter = Accepter()
accepter.content.add(55L, 66L)
accepter_list.append(accepter)
example_db[E_Cmd.Accepter] = accepter_list

def generator():
    """Iterable over all commands from the example_db.
    """
    index = 0
    for example_list in example_db.itervalues():
        for example in example_list:
            index += 1
            yield index, example

def get_two_lists(FirstSize):
    selectable = generator()

    first_list = []
    for i, cmd in selectable:
        if i == FirstSize: break
        first_list.append(cmd)

    second_list = [ cmd ]
    for i, cmd in selectable:
        second_list.append(cmd)

    return first_list, second_list

def rw_generator(N):
    """Iterable over all commands from the example_db.
    """
    for write_n in xrange(N):
        base = ["R"] + [" "] * (N - write_n - 1) + ["W"] * write_n
        for setting in set(permutations(base, N)):
            yield setting 

def rw_get(Flag):
    if   Flag == "R": return Assign(E_R.InputP,       E_R.LexemeStartP)
    elif Flag == "W": return Assign(E_R.LexemeStartP, E_R.InputP)
    else:             return Assign(E_R.Column,       E_R.CharacterBeginP)

def string_cl(Name, Cl):
    if len(Cl) == 0:
        return "    %s: <empty>" % Name
    txt = "    %s: [0] %s\n" % (Name, Cl[0])
    for i, cmd in enumerate(Cl[1:]):
        txt += "       [%i] %s\n" % (i+1, cmd)
    return txt

def print_cl(Name, Cl):
    print string_cl(Name, Cl)
