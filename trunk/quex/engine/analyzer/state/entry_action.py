from   quex.blackboard          import setup as Setup, \
                                       E_StateIndices, E_PreContextIDs, E_TriggerIDs
from   quex.engine.misc.file_in import error_msg
from   quex.engine.tools        import pair_combinations, TypedSet
from   quex.engine.misc.enum    import Enum
from   quex.blackboard          import E_AcceptanceIDs, E_DoorIdIndex

from   collections              import defaultdict, namedtuple
from   operator                 import attrgetter, itemgetter
from   copy                     import deepcopy, copy
from   itertools                import islice, izip

class DoorID(namedtuple("DoorID_tuple", ("state_index", "door_index"))):
    def __new__(self, StateIndex, DoorIndex):
        assert isinstance(StateIndex, (int, long)) or StateIndex in E_StateIndices or StateIndex == E_AcceptanceIDs.FAILURE
        # 'DoorIndex is None' --> right after the entry commands (targetted after reload).
        assert isinstance(DoorIndex, (int, long))  or DoorIndex is None or DoorIndex in E_DoorIdIndex, "%s" % DoorIndex
        return super(DoorID, self).__new__(self, StateIndex, DoorIndex)

    @staticmethod
    def drop_out(StateIndex):             return DoorID(StateIndex, E_DoorIdIndex.DROP_OUT)
    @staticmethod                        
    def transition_block(StateIndex):     return DoorID(StateIndex, E_DoorIdIndex.TRANSITION_BLOCK)
    @staticmethod                        
    def global_state_router():            return DoorID(0,          E_DoorIdIndex.GLOBAL_STATE_ROUTER)
    @staticmethod                        
    def acceptance(PatternId):                                return DoorID(PatternId,  E_DoorIdIndex.ACCEPTANCE)
    @staticmethod                        
    def state_machine_entry(SM_Id):                           return DoorID(SM_Id,  E_DoorIdIndex.STATE_MACHINE_ENTRY)
    @staticmethod                        
    def backward_input_position_detector_return(PatternId):   return DoorID(PatternId,  E_DoorIdIndex.BIPD_RETURN)
    @staticmethod                         
    def global_end_of_pre_context_check(): return DoorID(0,         E_DoorIdIndex.GLOBAL_END_OF_PRE_CONTEXT_CHECK)
    @staticmethod                         
    def global_terminal_router():         return DoorID(0,          E_DoorIdIndex.GLOBAL_TERMINAL_ROUTER)
    @staticmethod                         
    def global_terminal_end_of_file():    return DoorID(0,          E_DoorIdIndex.GLOBAL_TERMINAL_END_OF_FILE)
    @staticmethod
    def global_reentry():                 return DoorID(0,          E_DoorIdIndex.GLOBAL_REENTRY)
    @staticmethod
    def global_reentry_preparation():     return DoorID(0,          E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION)
    @staticmethod
    def global_reentry_preparation_2():   return DoorID(0,          E_DoorIdIndex.GLOBAL_REENTRY_PREPARATION_2)

    def drop_out_f(self):    return self.door_index == E_DoorIdIndex.DROP_OUT

    def __repr__(self):
        return "DoorID(s=%s, d=%s)" % (self.state_index, self.door_index)

class DoorID_Scheme(tuple):
    """A TargetByStateKey maps from a index, i.e. a state_key to a particular
       target (e.g. a DoorID). It is implemented as a tuple which can be 
       identified by the class 'TargetByStateKey'.
    """
    def __new__(self, DoorID_List):
        return tuple.__new__(self, DoorID_List)

    @staticmethod
    def concatinate(This, That):
        door_id_list = list(This)
        door_id_list.extend(list(That))
        return DoorID_Scheme(door_id_list)

class TransitionID(namedtuple("TransitionID_tuple", ("target_state_index", "source_state_index", "trigger_id"))):
    """Objects of this type identify a transition. 
    
                   .----- trigger_id ---->-[ TransitionAction ]----.
                   |                                               |
        .--------------------.                          .--------------------.
        | source_state_index |                          | target_state_index |
        '--------------------'                          '--------------------'
    
       NOTE: There might be multiple transitions from source to target. Each transition
             has another trigger_id. The relation between a TransitionID and a 
             TransitionAction is 1:1.

    """
    def __new__(self, StateIndex, FromStateIndex, TriggerId):
        assert isinstance(StateIndex, (int, long))     or StateIndex     in E_StateIndices
        assert isinstance(FromStateIndex, (int, long)) or FromStateIndex in E_StateIndices
        assert isinstance(TriggerId, (int, long))      or TriggerId      in E_TriggerIDs
        return super(TransitionID, self).__new__(self, StateIndex, FromStateIndex, TriggerId)

    def is_from_reload(self):
        return   self.source_state_index == E_StateIndices.RELOAD_FORWARD \
              or self.source_state_index == E_StateIndices.RELOAD_BACKWARD

    def __repr__(self):
        source_state_str = "%s" % self.source_state_index

        if self.trigger_id == 0:
            return "TransitionID(to=%s, from=%s)" % (self.target_state_index, source_state_str)
        else:
            return "TransitionID(to=%s, from=%s, trid=%s)" % (self.target_state_index, source_state_str, self.gtrigger_id)

class TransitionAction(object):
    """Object containing information about commands to be executed upon
       transition into a state.

       .command_list  --> list of commands to be executed upon the transition.
       .door_id       --> An 'id' which is supposed to be unique for a command list. 
                          It is (re-)assigned during the process of 
                          'EntryActionDB.categorize()'.
    """
    __slots__ = ("door_id", "command_list")
    def __init__(self, CommandListObjectF=True):
        # NOTE: 'DoorId' is not accepted as argument. Is needs to be assigned
        #       by '.categorize()' in the action_db. Then, transition actions
        #       with the same CommandList-s share the same DoorID.
        assert type(CommandListObjectF) == bool
        self.door_id = None # DoorID into door tree from where the command list is executed
        if CommandListObjectF: self.command_list = CommandList() 
        else:                  self.command_list = None
 
    def clone(self):
        result = TransitionAction(CommandListObjectF=False)
        result.door_id      = self.door_id  # DoorID-s are immutable
        result.command_list = self.command_list.clone()
        return result

    # Make TransitionAction usable for dictionary and set
    def __hash__(self):      
        return hash(self.command_list)

    def __eq__(self, Other):
        return self.command_list == Other.command_list

    def __repr__(self):
        return "(%s: [%s])" % (self.door_id, self.command_list)

E_Commands = Enum("StoreInputPosition",
                  "PreConditionOK",
                  "TemplateStateKeySet",
                  "PathIteratorSet",
                  "PathIteratorIncrement",
                  "PrepareAfterReload",
                  "PrepareAfterReload_InitState",
                  "InputPIncrement",
                  "InputPDecrement",
                  "InputPDereference",
                  "_DEBUG_Commands")

# To come:
# CountColumnN_ReferenceSet
# CountColumnN_ReferenceAdd
# CountColumnN_Add
# CountColumnN_Grid
# CountLineN_Add

class Command(object):
    __slots__ = ("id", "level", "cost", "content", "_hash")
    MaxLevelN = 2

    db = {
        E_Commands.StoreInputPosition:            (0, 1, namedtuple("C0", "pre_context_id", "position_register", "offset")),
        E_Commands.PreConditionOK:                (0, 1, namedtuple("C1", "pre_context_id")),
        E_Commands.TemplateStateKeySet:           (0, 1, namedtuple("C2", "state_key")),
        E_Commands.PathIteratorSet:               (0, 1, namedtuple("C3", "path_walker_id", "path_id", "offset")),
        E_Commands.PathIteratorIncrement:         (0, 1, None),
        E_Commands.PrepareAfterReload:            (0, 1, namedtuple("C4", "state_index")),
        E_Commands.PrepareAfterReload_InitState:  (0, 1, namedtuple("C5", "state_index")),
        E_Commands.InputPIncrement:               (1, 1, None),
        E_Commands.InputPDecrement:               (1, 1, None),
        E_Commands.InputPDereference:             (2, 1, None),
    }

    def __init__(self, Id, *ParameterList):
        assert type(ParameterList) == tuple, "ParameterList: '%s'" % str(ParameterList)
        cmd_info   = Command.db[Id]
        self.id      = Id
        self.level   = cmd_info[0]
        self.cost    = cmd_info[1]
        L = len(ParameterList)
        if   L == 0: self.content = None
        elif L == 1: self.content = cmd_info[3](ParameterList[0])
        elif L == 2: self.content = cmd_info[3](ParameterList[0], ParameterList[1])
        elif L == 3: self.content = cmd_info[3](ParameterList[0], ParameterList[1], ParameterList[2])
        self._hash = hash(Id) ^ hash(self.content)

    def clone(self):         
        if   self._x is None:   return self.__class__()
        elif len(self._x) == 1: return self.__class__(self._x[0])
        elif len(self._x) == 2: return self.__class__(self._x[0], self._x[1])
        elif len(self._x) == 3: return self.__class__(self._x[0], self._x[1], self._x[2])
        else:                   assert False

    def __hash__(self):      
        return self._hash

    def __eq__(self, Other): 
        if   self.__class__ != Other.__class__: return False
        elif self.id        != Other.id:        return False
        assert self.level == Other.level and self.cost == Other.cost
        return self.content == Other.content

    def __str__(self):
        name_str    = str(self.id)
        content_str = "".join("%s=%s, " % (member, value) for member, value in self.content._asdict.iteritems())
        return "%s: { %s }" % (name_str, content_str)

# TODO: Consider 'Flyweight pattern'. Check wether object with same content exists, 
#       then return pointer to object in database.
def StoreInputPosition(PreContextID, PositionRegister, Offset):
    return Command(E_Commands.StoreInputPosition, PreContextID, PositionRegister, Offset)

def PreConditionOK(PreContextID):
    return Command(E_Commands.PreContextID, PreContextID)

def TemplateStateKeySet(StateKey):
    return Command(E_Commands.TemplateStateKeySet, StateKey)

def PathIteratorSet(PathWalkerID, PathID, Offset):
    return Command(E_Commands.PathIteratorSet, PathWalkerID, PathID, Offset)

def PathIteratorIncrement():
    return Command(E_Commands.PathIteratorIncrement)

def PrepareAfterReload():
    return Command(E_Commands.PrepareAfterReload, StateIndex)

def PrepareAfterReload_InitState():
    return Command(E_Commands.PrepareAfterReload_InitState, StateIndex)

def InputPIncrement():
    return Command(E_Commands.InputPIncrement)

def InputPDecrement():
    return Command(E_Commands.InputPDecrement)

def InputPDereference():
    return Command(E_Commands.InputPDereference)

class CommandList:
    def __init__(self):
        self.accepter = None
        self.level    = [] 
         
        for i in xrange(Command.MaxLevelN+1):
            self.level.append([]) # .level[i] --> Commands of level 'i'

    @classmethod
    def from_iterable(cls, Iterable):
        result = CommandList()
        for cmd in Iterable:
            assert isinstance(cmd, Command)
            if isinstance(cmd, Accepter):
                assert self.accepter is None
                result.accepter = cmd
            else:
                result.level[cmd.level].append(cmd)
        return result

    def add(self, Cmd):
        print "#level:", Cmd.level, self.level
        self.level[Cmd.level].append(Cmd)

    def clone(self):
        result = CommandList()
        if self.accepter is not None: result.accepter = self.accepter.clone()
        else:                         result.accepter = None
        for i in xrange(Command.MaxLevelN+1):
            result.level[i] = [ cmd.clone() for cmd in self.level[i] ]
        return result

    @staticmethod
    def intersection(This, That):
        result = CommandList()
        # If one has commands on higher level and the other not, then there is no 'sharing'
        # Level '0' can freely share
        for i in reversed(xrange(1, Command.MaxLevelN+1)):
            if This.level[i] != That.level[i]: break
            result.level[i] = [ x.clone() for x in That.level[i] ]

        if This.accepter is not None and This.accepter == That.accepter: result.accepter = This.accepter.clone()
        else:                                                            result.accepter = None
        return result

    def difference_update(self, Other):
        """Delete all commands from Other from this command list.
        """
        if self.accepter == Other.accepter: 
            self.accepter = None

        assert type(Other.misc) == set
        for cmd in Other.misc:
            assert isinstance(cmd, Command)

        self.misc.difference_update(Other.misc)

    def is_empty(self):
        if self.accepter is not None: return False
        return len(self.misc) == 0

    def cost(self):
        return sum(x.cost() for x in self)

    def __iter__(self):
        """Allow iteration over comand list."""
        if self.accepter is not None: 
            yield self.accepter

        for action in sorted(self.misc, key=attrgetter("level", "id")):
            yield action

    def __hash__(self):
        xor_sum = 0
        for x in self.misc:
            xor_sum ^= hash(x)

        if self.accepter is not None:
            xor_sum ^= hash(self.accepter)

        return xor_sum

    def __eq__(self, Other):
        # Rely on '__eq__' of Accepter
        if isinstance(Other, CommandList) == False: return False
        elif not (self.accepter == Other.accepter): return False
        else:                                       return self.misc == Other.misc

    def __ne__(self, Other):
        return not self.__eq__(Other)

    def __repr__(self):
        txt = ""
        if self.accepter is not None:
            txt += "a"
            for x in self.accepter:
                txt += "%s," % repr(x.pattern_id)

        for action in self.misc:
            txt += "%s" % action
        return txt

