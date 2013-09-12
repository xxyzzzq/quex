from   quex.blackboard          import setup as Setup, \
                                       E_StateIndices, E_PreContextIDs, E_TriggerIDs
from   quex.engine.misc.file_in import error_msg
from   quex.engine.tools        import pair_combinations, TypedSet
from   quex.engine.misc.enum    import Enum
from   quex.blackboard          import E_AcceptanceIDs, E_DoorIdIndex, E_Commands

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

# To come:
# CountColumnN_ReferenceSet
# CountColumnN_ReferenceAdd
# CountColumnN_Add
# CountColumnN_Grid
# CountLineN_Add

class Command(object):
    __slots__ = ("id", "level", "cost", "content", "_hash")
    def __init__(self, Id, Level, Content, Hash, Cost):
        self.id    = Id
        self.level = Level
        self.cost  = Cost
        self._hash = hash(Id) ^ hash(Content)
        self.x     = Content

    def clone(self):         
        if   self.x is None:   return Command(self.id)
        elif len(self.x) == 1: return Command(self.id, self.x[0])
        elif len(self.x) == 2: return Command(self.id, self.x[0], self.x[1])
        elif len(self.x) == 3: return Command(self.id, self.x[0], self.x[1], self.x[2])
        else:                  assert False

    def __hash__(self):      
        return self._hash

    def __eq__(self, Other): 
        if   self.__class__ != Other.__class__: return False
        elif self.id        != Other.id:        return False
        assert self.level == Other.level and self.cost == Other.cost
        return self.x == Other.x

    def __str__(self):
        name_str    = str(self.id)
        if self.x is None:
            content_str = ""
        else:
            content_str = "".join("%s=%s, " % (member, value) for member, value in self.x._asdict.iteritems())
        return "%s: { %s }" % (name_str, content_str)

# Accepter:
# 
# In this case the pre-context-id is essential. We cannot accept a pattern if
# its pre-context is not fulfilled.
AccepterElement = namedtuple("AccepterElement", ("pre_context_id", "pattern_id"))
class Accepter(Command):
    __slots__ = ["__list"]
    def __init__(self, PathTraceList=None):
        Command.__init__(self)
        if PathTraceList is None: 
            self.__list = []
        else:
            self.__list = [ AccepterElement(x.pre_context_id, x.pattern_id) for x in PathTraceList ]

    def clone(self):
        result = Accepter()
        result.__list = [ deepcopy(x) for x in self.__list ]
        return result
    
    def add(self, PreContextID, PatternID):
        self.__list.append(AccepterElement(PreContextID, PatternID))

    def clean_up(self):
        """Ensure that nothing follows and unconditional acceptance."""
        self.__list.sort(key=attrgetter("pattern_id"))
        for i, x in enumerate(self.__list):
            if x.pre_context_id == E_PreContextIDs.NONE:
                break
        if i != len(self.__list) - 1:
            del self.__list[i+1:]

    # Estimate cost for the accepter:
    # pre-context check + assign acceptance + conditional jump: 3
    # assign acceptance:                                        1
    def cost(self):
        result = 0
        for action in self.__list:
            if action.pre_context_id: result += 3
            else:                     result += 1
        return result

    # Require '__hash__' and '__eq__' to be element of a set.
    def __hash__(self): 
        xor_sum = 0
        for x in self.__list:
            if isinstance(x.pattern_id, (int, long)): xor_sum ^= x.pattern_id
        return xor_sum

    def __eq__(self, Other):
        if not isinstance(Other, Accepter):             return False
        if len(self.__list) != len(Other.__list):       return False
        for x, y in zip(self.__list, Other.__list):
            if   x.pre_context_id != y.pre_context_id:  return False
            elif x.pattern_id     != y.pattern_id:      return False
        return True

    def __iter__(self):
        for x in self.__list:
            yield x

    def __repr__(self):
        return "".join(["pre(%s) --> accept(%s)\n" % (element.pre_context_id, element.pattern_id) \
                       for element in self.__list])


class CommandFactory:
    LevelN    = 3

    db = {
        E_Commands.Accepter:                      (0, 1, Accepter),
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

    def do(self, Id, *ParameterList):
        # TODO: Consider 'Flyweight pattern'. Check wether object with same content exists, 
        #       then return pointer to object in database.
        assert type(ParameterList) == tuple, "ParameterList: '%s'" % str(ParameterList)
        cmd_info   = CommandFactory.db[Id]
        if   L == 0: content = None
        elif L == 1: content = cmd_info[2](ParameterList[0])
        elif L == 2: content = cmd_info[2](ParameterList[0], ParameterList[1])
        elif L == 3: content = cmd_info[2](ParameterList[0], ParameterList[1], ParameterList[2])

        return Command(Id, cmd_info[0], cmd_info[1], content)


def StoreInputPosition(PreContextID, PositionRegister, Offset):
    return CommandFactory.do(E_Commands.StoreInputPosition, PreContextID, PositionRegister, Offset)

def PreConditionOK(PreContextID):
    return CommandFactory.do(E_Commands.PreContextID, PreContextID)

def TemplateStateKeySet(StateKey):
    return CommandFactory.do(E_Commands.TemplateStateKeySet, StateKey)

def PathIteratorSet(PathWalkerID, PathID, Offset):
    return CommandFactory.do(E_Commands.PathIteratorSet, PathWalkerID, PathID, Offset)

def PathIteratorIncrement():
    return CommandFactory.do(E_Commands.PathIteratorIncrement)

def PrepareAfterReload(StateIndex):
    return CommandFactory(E_Commands.PrepareAfterReload, StateIndex)

def PrepareAfterReload_InitState(StateIndex):
    return CommandFactory(E_Commands.PrepareAfterReload_InitState, StateIndex)

def InputPIncrement():
    return CommandFactory(E_Commands.InputPIncrement)

def InputPDecrement():
    return CommandFactory(E_Commands.InputPDecrement)

def InputPDereference():
    return CommandFactory(E_Commands.InputPDereference)

class CommandList:
    """CommandList -- a list of commands.

    CommandList-s are subject to sharing. However, there are important
    rules, such as 'dereferencing a pointer comes after pointer increment'.
    To command lists A and B as in


           A:                         B:
           input_p => position        input_p => position
                                      input_p++

    cannot be combined into 

                    B: input_p++                  # ERROR
                    A: input_p => position        # ERROR

    because, then in case of B the input pointer is incremented BEFORE the
    position is stored. Since the dependencies are always the same, commands
    are associated with 'levels'. In the above example 'input_p++' has a
    higher level than 'input_p => position'. The following must hold:

          For every command Ca with a level La in a command list A,
          a command list B cannot share commands of level Lb < La
          if the command Ca is not in B.

    An exception are commands of level '-1' because they have no dependency,
    e.g. 'Accepter', 'PreConditionOK', 'TemplateStateKeySet' or 'PathIteratorSet'.
    """
    def __init__(self):
        self.level_db = defaultdict(list)

    @classmethod
    def from_iterable(cls, Iterable):
        result = CommandList()
        result.extend(Iterable)
        return result

    def add(self, Cmd):
        assert isinstance(cmd, Command)
        self.level_db[Cmd.level].append(Cmd)

    def extend(self, Iterable):
        for cmd in Iterable:
            self.add(Cmd)

    def clone(self):
        result = CommandList()
        for level, command_list in self.level_db.iteritems():
            result.level_db[level] = [ x.clone() for x in command_list ]
        return result

    @staticmethod
    def intersection(This, That):
        def iterable_shared(CLa, CLb):
            return (command for command in CLa if command in CLb)

        # Check what is shared on the '-1 level', i.e. the level without
        # dependencies.
        result = CommandList.from_iterable(iterable_shared(This.level_db[-1], That.level_db[-1]))

        this_level_list = sorted(This.level_db.keys())
        that_level_list = sorted(That.level_db.keys())
        while 1 + 1 == 2:
            if len(this_level_list) == 0 or len(that_level_list) == 0: 
                break
            level = this_level_list.pop()
            that_level_list.pop()
            result.extend(iterable_shared(This.level_db[level], That.level_db[level]))

        return result

    def difference_update(self, Other):
        """Delete all commands from Other from this command list.
        """
        for level, command_list in self.level_db.iteritems():
            other_command_list = Otherl.level_db[level]
            i = len(command_list) - 1
            while i >= 0:
                cmd = command_list[i]
                if cmd in other_command_list:
                    del command_list[i]
                i -= 1

    def is_empty(self):
        if self.accepter is not None: return False
        return len(self.misc) == 0

    def cost(self):
        return sum(x.cost() for x in self)

    def __iter__(self):
        """Allow iteration over comand list."""
        if self.accepter is not None: 
            yield self.accepter

        for i in reversed(xrange(Command.LevelN)):
            for action in sorted(self.level[i], key=attrgetter("id")):
                yield action

    def __hash__(self):
        xor_sum = 0
        for cmd in self:
            xor_sum ^= hash(x)
        return xor_sum

    def __eq__(self, Other):
        # Rely on '__eq__' of Accepter
        if isinstance(Other, CommandList) == False: return False
        return self.level_db == Other.level_db

    def __ne__(self, Other):
        return not self.__eq__(Other)

    def __repr__(self):
        txt = ""
        if self.accepter is not None:
            txt += "a"
            for x in self.accepter:
                txt += "%s," % repr(x.pattern_id)

        for i in reversed(xrange(Command.LevelN)):
            for action in self.level[i]:
                txt += "%s" % action
        return txt

