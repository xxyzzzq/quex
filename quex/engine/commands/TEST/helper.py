from   quex.engine.commands.content_terminal_router         import *
from   quex.engine.commands.core         import *
from   quex.engine.commands.core         import _cost_db
from   quex.engine.analyzer.door_id_address_label import DoorID
import quex.engine.commands.shared_tail  as command_list_shared_tail
import quex.engine.analyzer.engine_supply_factory as     engine
from   quex.output.core.dictionary       import db

from   quex.blackboard import E_Cmd, \
                              E_R, \
                              E_Compression, \
                              setup as Setup, \
                              Lng

from   itertools   import permutations
from   collections import defaultdict
from   copy        import deepcopy
from   random      import shuffle


Setup.language_db = db[Setup.language]

example_db = {
    E_Cmd.StoreInputPosition: [ 
        Command.StoreInputPosition(4711, 7777, 0),
        Command.StoreInputPosition(4711, 7777, 1000) 
    ],
    E_Cmd.PreContextOK:                     [ Command.PreContextOK(4711) ],
    E_Cmd.TemplateStateKeySet:              [ Command.TemplateStateKeySet(66) ],
    E_Cmd.PathIteratorSet:                  [ Command.PathIteratorSet(11, 22, 1000) ],
    E_Cmd.PrepareAfterReload:               [ Command.PrepareAfterReload(DoorID(33, 44), DoorID(55, 66)) ],
    E_Cmd.InputPIncrement:                  [ Command.InputPIncrement() ],
    E_Cmd.InputPDecrement:                  [ Command.InputPDecrement() ],
    E_Cmd.InputPDereference:                [ Command.InputPDereference() ],
    E_Cmd.LexemeResetTerminatingZero:       [ Command.LexemeResetTerminatingZero() ],
    E_Cmd.ColumnCountReferencePSet:         [ Command.ColumnCountReferencePSet(E_R.CharacterBeginP, 1000) ],
    E_Cmd.ColumnCountReferencePDeltaAdd:    [ Command.ColumnCountReferencePDeltaAdd(E_R.CharacterBeginP, 5555, False) ],
    E_Cmd.ColumnCountAdd:                   [ Command.ColumnCountAdd(1) ],
    E_Cmd.ColumnCountGridAdd: [ 
        Command.ColumnCountGridAdd(1),
        Command.ColumnCountGridAdd(2),
        Command.ColumnCountGridAdd(3),
        Command.ColumnCountGridAdd(4),
        Command.ColumnCountGridAdd(5),
    ],
    E_Cmd.LineCountAdd: [ Command.LineCountAdd(1) ],
    ## The column number is set to 1 at the newline.
    ## So, no the delta add 'column += (p - reference_p) * c' is not necessary.
    E_Cmd.GotoDoorId:                        [ Command.GotoDoorId(DoorID(33,44)) ],
    E_Cmd.GotoDoorIdIfInputPNotEqualPointer: [ Command.GotoDoorIdIfInputPNotEqualPointer(DoorID(33,44), E_R.CharacterBeginP) ],
    E_Cmd.Assign:                            [ Command.Assign(E_R.InputP, E_R.LexemeStartP) ],
    E_Cmd.AssignConstant: [ 
        Command.AssignConstant(E_R.InputP, 0), 
        Command.AssignConstant(E_R.ReferenceP, 1), 
        Command.AssignConstant(E_R.Column, 2), 
    ],
    E_Cmd.IfPreContextSetPositionAndGoto: [
        Command.IfPreContextSetPositionAndGoto(24, RouterContentElement(66, 1)),
    ],
    E_Cmd.IndentationHandlerCall: [ 
        Command.IndentationHandlerCall(True, "SLEEPY"),
        Command.IndentationHandlerCall(False, "EXITED"),
    ],
    E_Cmd.QuexAssertNoPassage: [
        Command.QuexAssertNoPassage(),
    ],
    E_Cmd.QuexDebug: [
        Command.QuexDebug("Hello Bug!"),
    ],
    E_Cmd.RouterOnStateKey: [
        Command.RouterOnStateKey(E_Compression.PATH, 0x4711L, 
                         [(1L, 100L), (2L, 200L), (3L, 300L)], 
                         lambda x: DoorID(x,1)),
    ],
}

accepter = Command.Accepter()
accepter.content.add(55L, 66L)
example_db[E_Cmd.Accepter] = [ accepter ]

router = Command.Router()
router.content.add(66, 1)
example_db[E_Cmd.Router] = [ router ]

def generator():
    """Iterable over all commands from the example_db.
    """
    index = 0
    for example_list in example_db.itervalues():
        for example in example_list:
            index += 1
            yield index, example

def generator_n(N, Begin=0):
    index = -1
    while 1 + 1 == 2:
        for i, cmd in generator():
            index += 1
            if   index < Begin:      continue
            elif index == N + Begin: return
            yield cmd

def random_command_list(N, Seed):
    return [ cmd for cmd in generator_n(N, Seed) ]

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
    if   Flag == "R": return Command.Assign(E_R.InputP,       E_R.LexemeStartP)
    elif Flag == "W": return Command.Assign(E_R.LexemeStartP, E_R.InputP)
    else:             return Command.Assign(E_R.Column,       E_R.CharacterBeginP)

def string_cl(Name, Cl):
    if len(Cl) == 0:
        return "    %s: <empty>" % Name
    txt = "    %s: [0] %s\n" % (Name, Cl[0])
    for i, cmd in enumerate(Cl[1:]):
        txt += "       [%i] %s\n" % (i+1, cmd)
    return txt

def print_cl(Name, Cl):
    print string_cl(Name, Cl)

class MiniAnalyzer:
    def __init__(self):
        self.engine_type = engine.FORWARD

Lng.register_analyzer(MiniAnalyzer())
