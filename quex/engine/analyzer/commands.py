# MAIN CLASSES:
#
# (*) Command:
#
#     .id      -- identifies the command (from E_Commands)
#     .content -- 'Arguments' and/or additional information
#                 (Normally a tuple, 'AccepterContent' is a real class).
#  
# (*) CommandFactory:
#
#     Contains the database of all available commands. The '.do()' member
#     function can generate a command based on a set of arguments and 
#     the command's identifier.
#
#     CommandInfo:
#
#     Tells about the attributes of each command, i.e. its 'cost', its access
#     type (read/write/none) a constructor for the class of the '.content'
#     member.
#
#     CommandFactory.db:
#
#               Command identifier ----> CommandInfo
#
#     Maps from a command identifier (see E_Commands) to a CommandInfo. The
#     CommandInfo is used to create a Command.
#
# (*) CommandList:
#
#     A class which represents a sequence of Command-s. There is one special
#     function in this class '.get_shared_tail(Other)' which allows to find
#     find shared Command-s in 'self' and 'Other' so that each CommandList
#     can do its own Command-s followed by the shared tail. 
#
#     This 'shared tail' is used for the 'door tree construction'. That is, 
#     upon entry into a state the CommandList-s may different dependent on
#     the source state, but some shared commands may be the same. Those
#     shared commands are then only implemented once and not for each source
#     state separately.
#______________________________________________________________________________
#
# EXPLANATION:
#
# Command-s represent operations such as 'Accept X if Pre-Context Y fulfilled'
# or 'Store Input Position in Position Register X'. They are used to control
# basic operations of the pattern matching state machine.
#
# A command is generated by the CommandFactory's '.do(id, parameters)'
# function. For clarity, dedicated functions may be used, do provide a more
# beautiful call to the factory, for example:
#
#     cmd = StoreInputPosition(PreContextID, PositionRegister, Offset)
#
# is equivalent to
#
#     cmd = CommandFactory.do(E_Commands.StoreInputPosition, 
#                             (PreContextID, PositionRegister, Offset))
#
# where, undoubtedly the first is much easier to read. 
#
# ADAPTATION:
#
# The list of commands is given by 'E_Commands' and the CommandFactory's '.db' 
# member. That is, to add a new command requires an identifier in E_Commands,
# and an entry in the CommandFactory's '.db' which associates the identifier
# with a CommandInfo. Additionally, the call to the CommandFactory may be 
# abbreviated by a dedicated function as in the example above.
#______________________________________________________________________________
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
from   quex.engine.misc.enum import Enum
from   quex.blackboard       import E_Commands, \
                                    E_PreContextIDs

from   collections import namedtuple
from   operator    import attrgetter
from   copy        import deepcopy, copy

#______________________________________________________________________________
# Command: Information about an operation to be executed. It consists mainly
#     of a command identifier (from E_Commands) and the content which specifies
#     the command further.
#______________________________________________________________________________
class Command(namedtuple("Command_tuple", ("id", "content", "my_hash"))):
    def __new__(self, Id, Content, Hash=None):
        if Hash is None: Hash = hash(Id) ^ hash(Content)
        return super(Command, self).__new__(self, Id, Content, Hash)

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

#______________________________________________________________________________
#
# AccepterContent(virtually Command): A list of conditional pattern acceptance 
#     actions. It corresponds to a sequence of if-else statements such as 
#
#       [0]  if   pre_condition_4711_f: acceptance = Pattern32
#       [1]  elif pre_condition_512_f:  acceptance = Pattern21
#       [2]  else:                      acceptance = Pattern56
# 
# AccepterContentElement: An element in the sorted list of test/accept commands. 
#     It contains the 'pre_context_id' of the condition to be checked and the 
#     'pattern_id' to be accepted if the condition is true.
#______________________________________________________________________________
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

#______________________________________________________________________________
# CommandInfo: Information about a command. CommandInfo-s provide information
#     about commands based on the command identifier. That is:
#
#     .cost         -- The computational cost of the operation.
#     .access       -- What it access and whether it is read or write.
#     .content_type -- Information so that the 'CommandFactory' can generate
#                      a command based on the command identifier.
#______________________________________________________________________________
class CommandInfo(namedtuple("CommandInfo_tuple", ("cost", "access", "content_type"))):
    def __new__(self, Cost, Access, ContentType=None):
        if type(ContentType) == tuple: content_type = namedtuple("Command_tuple", ContentType)
        else:                          content_type = ContentType
        return super(CommandInfo, self).__new__(self, Cost, Access, content_type)

    @property
    def read_f(self):  return self.access == E_InputPAccess.READ

    @property
    def write_f(self): return self.access == E_InputPAccess.WRITE

#______________________________________________________________________________
# CommandFactory: Produces Command-s. It contains a database which maps from 
#     command identifiers to CommandInfo-s. And, it contains the '.do()' 
#     function which produces Command-s.
#
# For a sleeker look, dedicated function are provided below which all implement
# a call to 'CommandFactory.do()' in a briefer way.
#______________________________________________________________________________
class CommandFactory:
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
        # CountColumnN_ReferenceSet
        # CountColumnN_ReferenceAdd
        # CountColumnN_Add
        # CountColumnN_Grid
        # CountLineN_Add
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

