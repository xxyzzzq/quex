from   quex.blackboard          import setup as Setup, \
                                       E_StateIndices, E_PreContextIDs, E_TriggerIDs
from   quex.engine.misc.file_in import error_msg
from   quex.engine.tools        import pair_combinations, TypedSet
from   quex.engine.misc.enum    import Enum
from   quex.blackboard          import E_AcceptanceIDs, E_DoorIdIndex, E_Commands

from   collections              import defaultdict, namedtuple
from   operator                 import attrgetter, itemgetter
from   copy                     import deepcopy, copy
from   itertools                import islice, izip, chain

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

class Command(namedtuple("Command_tuple", ("id", "content", "my_hash"))):
    def __new__(self, Id, Content):
        return super(Command, self).__new__(self, Id, Content, hash(Id) ^ hash(Content))

    def clone(self):         
        if hasattr(self.content, "clone"): 
            content = self.content.clone()
        else:
            content = tuple(copy(x) for x in self.content)
        return Command(self.id, content, self.my_hash, self.cost)

    def __hash__(self):      
        return self.my_hash

    def __str__(self):
        name_str = str(self.id)
        if self.content is None:
            return "%s" % name_str
        else:
            content_str = "".join("%s=%s, " % (member, value) for member, value in self.content._asdict().iteritems())
            return "%s: { %s }" % (name_str, content_str)

# AccepterContent: A list of conditional pattern acceptance actions. It corresponds
#           to a sequence of if-else statements such as 
#
#         if   pre_condition_4711_f: acceptance = Pattern32
#         elif pre_condition_512_f:  acceptance = Pattern21
#         else:                      acceptance = Pattern56
# 
# AccepterContentElement: An element in the sorted list of test/accept commands. It
#                  contains the 'pre_context_id' of the condition to be checked
#                  and the 'pattern_id' to be accepted if the condition is true.
#
AccepterContentElement = namedtuple("AccepterContentElement", ("pre_context_id", "pattern_id"))
class AccepterContent:
    def __init__(self, PathTraceList=None):
        Command.__init__(self)
        if PathTraceList is None: 
            self.__list = []
        else:
            self.__list = [ AccepterContentElement(x.pre_context_id, x.pattern_id) for x in PathTraceList ]

    def clone(self):
        result = AccepterContent()
        result.__list = [ deepcopy(x) for x in self.__list ]
        return result
    
    def add(self, PreContextID, PatternID):
        self.__list.append(AccepterContentElement(PreContextID, PatternID))

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
        if not isinstance(Other, AccepterContent):             return False
        if len(self.__list) != len(Other.__list):       return False
        for x, y in zip(self.__list, Other.__list):
            if   x.pre_context_id != y.pre_context_id:  return False
            elif x.pattern_id     != y.pattern_id:      return False
        return True

    def __iter__(self):
        for x in self.__list:
            yield x

    def __str__(self):
        return "".join(["pre(%s) --> accept(%s)\n" % (element.pre_context_id, element.pattern_id) \
                       for element in self.__list])


E_InputPAccess = Enum("WRITE",     # writes value to 'x'
                      "READ",      # reads value of 'x'
                      "NONE",      # does nothing to 'x'
                      "E_InputAccess_DEBUG")

class CommandInfo(namedtuple("CommandInfo_tuple", ("cost", "write_f", "read_f", "content_type"))):
    def __new__(self, Cost, Access, ContentType=None):
        if type(ContentType) == tuple: content_type = namedtuple("Command_tuple", ContentType)
        else:                          content_type = ContentType
        return super(CommandInfo, self).__new__(self, 
                                                Cost, 
                                                Access == E_InputPAccess.WRITE, # write_f
                                                Access == E_InputPAccess.READ,  # read_f
                                                content_type)

class CommandFactory:
    LevelN    = 3

    db = {
        E_Commands.Accepter:                      CommandInfo(1, E_InputPAccess.NONE,  AccepterContent),
        E_Commands.StoreInputPosition:            CommandInfo(1, E_InputPAccess.READ,  ("pre_context_id", "position_register", "offset")),
        E_Commands.PreConditionOK:                CommandInfo(1, E_InputPAccess.NONE,  ("pre_context_id",)),
        E_Commands.TemplateStateKeySet:           CommandInfo(1, E_InputPAccess.NONE,  ("state_key",)),
        E_Commands.PathIteratorSet:               CommandInfo(1, E_InputPAccess.NONE,  ("path_walker_id", "path_id", "offset")),
        E_Commands.PrepareAfterReload:            CommandInfo(1, E_InputPAccess.NONE,  ("state_index",)),
        E_Commands.PrepareAfterReload_InitState:  CommandInfo(1, E_InputPAccess.NONE,  ("state_index",)),
        E_Commands.InputPIncrement:               CommandInfo(1, E_InputPAccess.WRITE),
        E_Commands.InputPDecrement:               CommandInfo(1, E_InputPAccess.WRITE),
        E_Commands.InputPDereference:             CommandInfo(1, E_InputPAccess.READ),
    }

    @staticmethod
    def do(Id, ParameterList=None):
        # TODO: Consider 'Flyweight pattern'. Check wether object with same content exists, 
        #       then return pointer to object in database.
        assert ParameterList is None or type(ParameterList) == tuple, "ParameterList: '%s'" % str(ParameterList)
        content_type = CommandFactory.db[Id].content_type
        if ParameterList is None:
            content = None
        else:
            L        = len(ParameterList)
            if   L == 0: content = None
            elif L == 1: content = content_type(ParameterList[0])
            elif L == 2: content = content_type(ParameterList[0], ParameterList[1])
            elif L == 3: content = content_type(ParameterList[0], ParameterList[1], ParameterList[2])
        return Command(Id, content)

def StoreInputPosition(PreContextID, PositionRegister, Offset):
    return CommandFactory.do(E_Commands.StoreInputPosition, (PreContextID, PositionRegister, Offset))

def PreConditionOK(PreContextID):
    return CommandFactory.do(E_Commands.PreContextID, (PreContextID))

def TemplateStateKeySet(StateKey):
    return CommandFactory.do(E_Commands.TemplateStateKeySet, (StateKey))

def PathIteratorSet(PathWalkerID, PathID, Offset):
    return CommandFactory.do(E_Commands.PathIteratorSet, (PathWalkerID, PathID, Offset))

def PathIteratorIncrement():
    return CommandFactory.do(E_Commands.PathIteratorIncrement)

def PrepareAfterReload(StateIndex):
    return CommandFactory.do(E_Commands.PrepareAfterReload, (StateIndex))

def PrepareAfterReload_InitState(StateIndex):
    return CommandFactory.do(E_Commands.PrepareAfterReload_InitState, (StateIndex))

def InputPIncrement():
    return CommandFactory.do(E_Commands.InputPIncrement)

def InputPDecrement():
    return CommandFactory.do(E_Commands.InputPDecrement)

def InputPDereference():
    return CommandFactory.do(E_Commands.InputPDereference)

def Accepter():
    return CommandFactory.do(E_Commands.Accepter)

class CommandList(list):
    """CommandList -- a list of commands.
    """
    def __init__(self):
        list.__init__(self)

    @classmethod
    def from_iterable(cls, Iterable):
        result = CommandList()
        result.extend(Iterable)
        return result

    def clone(self):
        return CommandList.from_iterable(self)

    @staticmethod
    def get_shared_tail(This, That):
        """DEFINITION 'shared tail':
        
        ! A 'shared tail' is a list of commands. For each command of a        !
        ! shared tail, it holds that:                                         !
        !                                                                     !
        !  -- it appears in 'This' and 'That'.                                !
        !  -- if it is a 'WRITE', there is no related 'READ' or 'WRITE'       !
        !     command in This or That coming after the shared command.        !
        !  -- if it is a 'READ', there no related 'WRITE' command in          !
        !     This or That coming after the shared command.                   !

        The second and third condition is essential, so that the shared tail
        can be implemented from a joining point between 'This' and 'That'.
        Consider

            This:                               That:
            * position = input_p # READ         * position = input_p;
            * ++input_p          # WRITE        * input = *input_p;
            * input = *input_p;                      

        The 'position = input_p' cannot appear after '++input_p'. Let input_p
        be 'x' at the entry of This and That. This and That, both result in
        'position = x'. Then a combination, however, without second and third 
        condition results in

            This:                           That:
            * ++input_p;         # READ     * input = *input_p;
            * input = *input_p;                /
                          \                   /
                           \                 /
                          * position = input_p;   # WRITE (Error for This)

        which in the case of 'This' results in 'position = x + 1' (ERROR).
        """
        def is_related_to_unshared_write(CmdI, CmdList, SharedISet):
            for i in xrange(CmdI+1, len(CmdList)):
                cmd = CmdList[i]
                if CommandFactory.db[cmd.id].write_f and i not in SharedISet: 
                    return True
            return False

        def is_related_to_unshared_read_write(CmdI, CmdList, SharedISet):
            for i in xrange(CmdI+1, len(CmdList)):
                cmd = CmdList[i]
                if (CommandFactory.db[cmd.id].write_f or CommandFactory.db[cmd.id].read_f) and i not in SharedISet: 
                    return True
            return False

        shared_list = []
        done_k      = set() # The same command cannot be shared twice
        for i, cmd_a in enumerate(This):
            for k, cmd_b in enumerate(That):
                if   k in done_k:    continue
                elif cmd_a != cmd_b: continue
                print "#cmd_class:", cmd_a.__class__
                shared_list.append((cmd_a, i, k))
                done_k.add(k) # Command 'k' has been shared. Prevent sharing twice.
                break         # Command 'i' hass been shared, continue with next 'i'.

        change_f = True
        while change_f:
            change_f     = False
            shared_i_set = set(x[1] for x in shared_list)
            shared_k_set = set(x[2] for x in shared_list)
            i            = len(shared_list) - 1
            while i >= 0:
                print "#shared_list:", shared_list
                candidate, this_i, that_k = shared_list[i]
                if     CommandFactory.db[candidate.id].write_f \
                   and (   is_related_to_unshared_read_write(this_i, This, shared_i_set) \
                        or is_related_to_unshared_read_write(that_k, That, shared_k_set)):
                    del shared_list[i]
                    change_f = True
                if     CommandFactory.db[candidate.id].read_f \
                   and (   is_related_to_unshared_write(this_i, This, shared_i_set) \
                        or is_related_to_unshared_write(that_k, That, shared_k_set)):
                    del shared_list[i]
                    change_f = True
                else:
                    pass
                i -= 1

        return CommandList.from_iterable(cmd for cmd, i, k in shared_list) 

    def cut_shared_tail(self, SharedTail):
        """Delete all commands of SharedTail from this command list.
        """
        i = list.__len__(self) - 1
        while i >= 0:
            if self[i] in SharedTail:
                del self[i]
            i -= 1

    def is_empty(self):
        return list.__len__(self)

    def cost(self):
        return sum(x.cost() for x in self)

    def __hash__(self):
        xor_sum = 0
        for cmd in self:
            xor_sum ^= hash(x)
        return xor_sum

    def __eq__(self, Other):
        # Rely on '__eq__' of AccepterContent
        if isinstance(Other, CommandList) == False: return False
        return list.__eq__(self, Other)

    def __ne__(self, Other):
        return not self.__eq__(Other)

    def __str__(self):
        return "".join("%s\n" % str(cmd) for cmd in self)

