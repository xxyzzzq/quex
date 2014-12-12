# MAIN CLASSES:
#
# (*) Op:
#
#     .id      -- identifies the command (from E_Op)
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
#               Op identifier ----> CommandInfo
#
#     Maps from a command identifier (see E_Op) to a CommandInfo. The
#     CommandInfo is used to create a Op.
#
# (*) OpList:
#
#     A class which represents a sequence of Op-s. 
#
#     'command.shared_tail.get(A, B)' find shared Op-s in 'A' and 'B'.
#
#     This 'shared tail' is used for the 'door tree construction'. That is, 
#     upon entry into a state the OpList-s may different dependent on
#     the source state, but some shared commands may be the same. Those
#     shared commands are then only implemented once and not for each source
#     state separately.
#______________________________________________________________________________
#
# EXPLANATION:
#
# Op-s represent operations such as 'Accept X if Pre-Context Y fulfilled'
# or 'Store Input Position in Position Register X'. They are used to control
# basic operations of the pattern matching state machine.
#
# A command is generated by the CommandFactory's '.do(id, parameters)'
# function. For clarity, dedicated functions may be used, do provide a more
# beautiful call to the factory, for example:
#
#     cmd = Op.StoreInputPosition(PreContextID, PositionRegister, Offset)
#
# is equivalent to
#
#     cmd = CommandFactory.do(E_Op.StoreInputPosition, 
#                             (PreContextID, PositionRegister, Offset))
#
# where, undoubtedly the first is much easier to read. 
#
# ADAPTATION:
#
# The list of commands is given by 'E_Op' and the CommandFactory's '.db' 
# member. That is, to add a new command requires an identifier in E_Op,
# and an entry in the CommandFactory's '.db' which associates the identifier
# with a CommandInfo. Additionally, the call to the CommandFactory may be 
# abbreviated by a dedicated function as in the example above.
#______________________________________________________________________________
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
from   quex.blackboard       import E_Op, \
                                    E_R, \
                                    E_PreContextIDs
from   quex.engine.operations.content_router_on_state_key import RouterOnStateKeyContent
from   quex.engine.operations.content_accepter            import AccepterContent, \
                                                                 repr_pre_context_id
from   quex.engine.operations.content_terminal_router     import RouterContent, \
                                                                 repr_position_register
from   quex.engine.misc.tools import delete_if

from   collections import namedtuple
from   copy        import deepcopy
import types
import numbers

class Op(namedtuple("Op_tuple", ("id", "content", "my_hash", "branch_f"))):
    """_________________________________________________________________________
    Information about an operation to be executed. It consists mainly of a 
    command identifier (from E_Op) and the content which specifies the command 
    further.
    ____________________________________________________________________________
    """
    # Commands which shall appear only once in a command list:
    unique_set     = (E_Op.TemplateStateKeySet, 
                      E_Op.PathIteratorSet)

    # Fly weight pattern: Immutable objects need to exist only once. Every 
    # other 'new operation' may refer to the existing object. 
    #
    # Not all commands are immutable!
    #
    # Distinguish between commands that are fly weight candidates by the set 
    # of fly-weight-able command identifier. Use a positive list, NOT a negative
    # list. That way, new additions do not enter accidently into the fly weight
    # set.
    fly_weight_set = (E_Op.InputPDecrement, 
                      E_Op.InputPIncrement, 
                      E_Op.InputPDereference)
    fly_weight_db  = {}

    def __new__(self, Id, *ParameterList):
        global _content_db
        global _access_db
        # Fly weight pattern: immutable objects instantiated only once.
        if Id in self.fly_weight_db: return self.fly_weight_db[Id]
        
        content_type = _content_db[Id]
        if content_type is None:
            # No content
            content = None
        elif isinstance(content_type, types.ClassType):
            # Use 'real' constructor
            content = content_type() 
        else:
            # A tuple that describes the usage of the 'namedtuple' constructor.
            L = len(ParameterList)
            assert L != 0
            if   L == 1: content = content_type(ParameterList[0])
            elif L == 2: content = content_type(ParameterList[0], ParameterList[1])
            elif L == 3: content = content_type(ParameterList[0], ParameterList[1], ParameterList[2])
            elif L == 4: content = content_type(ParameterList[0], ParameterList[1], ParameterList[2], ParameterList[3])

        hash_value = hash(Id) ^ hash(content)
        
        # -- determine whether command is subject to 'goto/branching'
        branch_f = Id in _brancher_set

        result = super(Op, self).__new__(self, Id, content, hash_value, branch_f)

        # Store fly-weight-able objects in database.
        if Id in self.fly_weight_set: self.fly_weight_db[Id] = result
        return result

    def clone(self):         
        # If the fly weight object exists, it must be in the database.
        if self.id in self.fly_weight_db:    return self
        elif hasattr(self.content, "clone"): content = self.content.clone()
        else:                                content = deepcopy(self.content)
        return super(Op, self).__new__(self.__class__, self.id, content, self.my_hash, self.branch_f)

    @staticmethod
    def StoreInputPosition(PreContextID, PositionRegister, Offset):
        return Op(E_Op.StoreInputPosition, PreContextID, PositionRegister, Offset)
    
    @staticmethod
    def PreContextOK(PreContextID):
        return Op(E_Op.PreContextOK, PreContextID)
    
    @staticmethod
    def TemplateStateKeySet(StateKey):
        return Op(E_Op.TemplateStateKeySet, StateKey)
    
    @staticmethod
    def PathIteratorSet(PathWalkerID, PathID, Offset):
        return Op(E_Op.PathIteratorSet, PathWalkerID, PathID, Offset)
    
    @staticmethod
    def PrepareAfterReload(OnSuccessDoorId, OnFailureDoorId):
        return Op(E_Op.PrepareAfterReload, OnSuccessDoorId, OnFailureDoorId)
    
    @staticmethod
    def InputPIncrement():
        return Op(E_Op.InputPIncrement)
    
    @staticmethod
    def InputPDecrement():
        return Op(E_Op.InputPDecrement)
    
    @staticmethod
    def InputPDereference():
        return Op(E_Op.InputPDereference)
    
    @staticmethod
    def LexemeResetTerminatingZero():
        return Op(E_Op.LexemeResetTerminatingZero)
    
    @staticmethod
    def ColumnCountReferencePSet(Pointer, Offset=0):
        return Op(E_Op.ColumnCountReferencePSet, Pointer, Offset)
    
    @staticmethod
    def ColumnCountReferencePDeltaAdd(Pointer, ColumnNPerChunk, SubtractOneF):
        return Op(E_Op.ColumnCountReferencePDeltaAdd, Pointer, ColumnNPerChunk, SubtractOneF)
    
    @staticmethod
    def ColumnCountAdd(Value):
        return Op(E_Op.ColumnCountAdd, Value)
    
    @staticmethod
    def IndentationHandlerCall(DefaultIhF, ModeName):
        return Op(E_Op.IndentationHandlerCall, DefaultIhF, ModeName)
    
    @staticmethod
    def IfPreContextSetPositionAndGoto(PreContextId, RouterElement):
        #if     PreContextId == E_PreContextIDs.NONE \
        #   and RouterElement.positioning == 0:
        #    return GotoDoorId(DoorID.incidence(RouterElement.acceptance_id))
            
        return Op(E_Op.IfPreContextSetPositionAndGoto,PreContextId, RouterElement)
    
    @staticmethod
    def ColumnCountGridAdd(GridSize):
        return Op(E_Op.ColumnCountGridAdd, GridSize)
    
    @staticmethod
    def LineCountAdd(Value):
        return Op(E_Op.LineCountAdd, Value)
    
    @staticmethod
    def GotoDoorId(DoorId):
        return Op(E_Op.GotoDoorId, DoorId)
    
    @staticmethod
    def GotoDoorIdIfInputPNotEqualPointer(DoorId, Pointer):
        return Op(E_Op.GotoDoorIdIfInputPNotEqualPointer, DoorId, Pointer)
    
    @staticmethod
    def Assign(TargetRegister, SourceRegister):
        return Op(E_Op.Assign, TargetRegister, SourceRegister)
    
    @staticmethod
    def AssignConstant(Register, Value):
        return Op(E_Op.AssignConstant, Register, Value)
    
    @staticmethod
    def Accepter():
        return Op(E_Op.Accepter)
    
    @staticmethod
    def RouterByLastAcceptance():
        return Op(E_Op.RouterByLastAcceptance)
    
    @staticmethod
    def RouterOnStateKey(CompressionType, MegaStateIndex, IterableStateKeyStateIndexPairs, DoorID_provider):
        result = Op(E_Op.RouterOnStateKey)
    
        result.content.configure(CompressionType, MegaStateIndex, 
                                 IterableStateKeyStateIndexPairs, DoorID_provider)
        return result
    
    @staticmethod
    def QuexDebug(TheString):
        return Op(E_Op.QuexDebug, TheString)
    
    @staticmethod
    def QuexAssertNoPassage():
        return Op(E_Op.QuexAssertNoPassage)

    def is_conditionless_goto(self):
        if self.id == E_Op.GotoDoorId: 
            return True
        elif self.id == E_Op.IfPreContextSetPositionAndGoto:
            return     self.content.pre_context_id == E_PreContextIDs.NONE \
                   and self.content.router_element.positioning == 0
        return False
    
    def get_register_access_iterable(self):
        """For each command there are access infos associated with registers. For example
        a command that writes into register 'X' associates 'write-access' with X.
    
        This is MORE than what is found in '_access_db'. This function may derive 
        information on accessed registers from actual 'content' of the Op.
        
        RETURNS: An iterable over pairs (register_id, access right) meaning that the
                 command accesses the register with the given access type/right.
        """
        global _access_db
    
        for register_id, access in _access_db[self.id].iteritems():
            if isinstance(register_id, numbers.Integral):
                register_id = self.content[register_id] # register_id == Argument number which contains E_R
            elif type(register_id) == tuple:
                main_id          = register_id[0]       # register_id[0] --> in E_R
                sub_reference_id = register_id[1]       # register_id[1] --> Argument number containing sub-id
                sub_id           = self.content[sub_reference_id]
                register_id = "%s:%s" % (main_id, sub_id)
            yield register_id, access
    
    def get_access_rights(self, RegisterId):
        """Provides information about how the command modifies the register
        identified by 'RegisterId'. The 'read/write' access information is 
        provided in form of an RegisterAccessRight object.
        
        This function MUST rely on 'get_register_access_iterable', because 
        register ids may be produced dynamically based on arguments to the 
        command.
        
        RETURNS: RegisterAccessRight for the given RegisterId.
                 None, if command does not modify the given register.
        """
        for register_id, access in self.get_register_access_iterable():
            if register_id == RegisterId: return access
        return None

    def __hash__(self):      
        return self.my_hash

    def __eq__(self, Other):
        if   self.__class__ != Other.__class__: return False
        elif self.id        != Other.id:        return False
        elif self.content   != Other.content:   return False
        else:                                   return True

    def __ne__(self, Other):
        return not (self == Other)

    def __str__(self):
        name_str = str(self.id)
        if self.content is None:
            return "%s" % name_str

        elif self.id == E_Op.StoreInputPosition:
            x = self.content
            txt = ""
            if x.pre_context_id != E_PreContextIDs.NONE:
                txt = "if '%s': " % repr_pre_context_id(x.pre_context_id)
            pos_str = repr_position_register(x.position_register)
            if x.offset == 0:
                txt += "%s = input_p;" % pos_str
            else:
                txt += "%s = input_p - %i;" % (pos_str, x.offset)
            return txt

        elif self.id == E_Op.Accepter:
            return str(self.content)

        elif self.id == E_Op.RouterByLastAcceptance:
            return str(self.content)

        elif self.id == E_Op.RouterOnStateKey:
            return str(self.content)

        elif self.id == E_Op.PreContextOK:
            return "pre-context-fulfilled = %s;" % self.content.pre_context_id

        else:
            content_str = "".join("%s=%s, " % (member, value) for member, value in self.content._asdict().iteritems())
            return "%s: { %s }" % (name_str, content_str)   

def is_switchable(A, B):
    """Determines whether the command A and command B can be switched
    in a sequence of commands. This is NOT possible if:

       -- A and B read/write to the same register. 
          Two reads to the same register are no problem.

       -- One of the commands is goto-ing, i.e. branching.
    """
    if A.branch_f or B.branch_f: return False

    for register_id, access_a in A.get_register_access_iterable():
        access_b = B.get_access_rights(register_id)
        if access_b is None:
            # Register from command A is not found in command B
            # => no restriction from this register.
            continue
        elif access_a.write_f or access_b.write_f:
            # => at least one writes.
            # Also:
            #   access_b not None => B accesses register_id (read, write, or both)
            #   access_a not None => A accesses register_id (read, write, or both)
            # 
            # => Possible cases here:
            #
            #     (A w,  B w), (A w,  B r), (A w,  B rw)
            #     (A r,  B w), (A r,  B r), (A r,  B rw)
            #     (A rw, B w), (A rw, B r), (A rw, B rw)
            #
            # In all those cases A and B depend on the order that they are executed.
            # => No switch possible
            return False
        else:
            continue

    return True



def __configure():
    """Configure the database for commands.
            
    cost_db:      CommandId --> computational cost.
    content_db:   CommandId --> related registers
    access_db:    CommandId --> access types of the command (read/write)
    brancher_set: set of commands which may cause jumps/gotos.
    """
    cost_db    = {}
    content_db = {}
    access_db  = {}    # map: register_id --> RegisterAccessRight
    #______________________________________________________________________________
    # 1        -> Read
    # 2        -> Write
    # 1+2 == 3 -> Read/Write
    r = 1                # READ
    w = 2                # WRITE
    RegisterAccessRight = namedtuple("AccessRight", ("write_f", "read_f"))

    class RegisterAccessDB(dict):
        def __init__(self, RegisterAccessInfoList):
            for info in RegisterAccessInfoList:
                register_id = info[0]
                rights      = info[1]
                if len(info) == 3: 
                    sub_id_reference = info[2]
                    register_id = (register_id, sub_id_reference)
                self[register_id] = RegisterAccessRight(rights & w, rights & r)

    brancher_set = set() # set of ids of branching/goto-ing commands.

    def c(OpId, ParameterList, *RegisterAccessInfoList):
        # -- access to related 'registers'
        access_db[OpId] = RegisterAccessDB(RegisterAccessInfoList)

        # -- parameters that specify the command
        if type(ParameterList) != tuple: content_db[OpId] = ParameterList # Constructor
        elif len(ParameterList) == 0:    content_db[OpId] = None
        else:                            content_db[OpId] = namedtuple("%s_content" % OpId, ParameterList)
        
        # -- computational cost of the command
        cost_db[OpId] = 1

        # -- determine whether command is subject to 'goto/branching'
        for register_id in (info[0] for info in RegisterAccessInfoList):
            if register_id == E_R.ThreadOfControl: brancher_set.add(OpId)

    c(E_Op.Accepter,                         AccepterContent, 
                                              (E_R.PreContextFlags,r), (E_R.AcceptanceRegister,w))
    c(E_Op.Assign,                           ("target", "source"), 
                                              (0,w),     (1,r))
    c(E_Op.AssignConstant,                   ("register", "value"), 
                                              (0,w))
    c(E_Op.PreContextOK,                     ("pre_context_id",), 
                                              (E_R.PreContextFlags,w))
    #
    c(E_Op.GotoDoorId,                        ("door_id",), 
                                               (E_R.ThreadOfControl,w))
    c(E_Op.GotoDoorIdIfInputPNotEqualPointer, ("door_id",                              "pointer"),
                                               (E_R.ThreadOfControl,w), (E_R.InputP,r), (1,r))
    #
    c(E_Op.StoreInputPosition,               (               "pre_context_id",        "position_register",       "offset"),
                                              (E_R.InputP,r), (E_R.PreContextFlags,r), (E_R.PositionRegister,w,1)) # Argument '1' --> sub_id_reference
    c(E_Op.IfPreContextSetPositionAndGoto,   ("pre_context_id", "router_element"),
                                              (E_R.PreContextFlags, r), (E_R.PositionRegister, r), (E_R.ThreadOfControl, w), 
                                              (E_R.InputP, r+w))
    c(E_Op.InputPDecrement,                  None, (E_R.InputP,r+w))
    c(E_Op.InputPIncrement,                  None, (E_R.InputP,r+w))
    c(E_Op.InputPDereference,                None, (E_R.InputP,r), (E_R.Input,w))
    #
    c(E_Op.LexemeResetTerminatingZero,       None, (E_R.LexemeStartP,r), (E_R.Buffer,w), (E_R.InputP,r), (E_R.Input,w))
    #
    c(E_Op.IndentationHandlerCall,           ("default_f", "mode_name"),
                                              (E_R.Column,r), (E_R.Indentation,r+w), (E_R.ReferenceP,r))
    #
    c(E_Op.ColumnCountAdd,                   ("value",),
                                              (E_R.Column,r+w))
    c(E_Op.ColumnCountGridAdd,               ("grid_size",),
                                              (E_R.Column,r+w))
    c(E_Op.ColumnCountReferencePSet,         ("pointer", "offset"),
                                              (0,r), (E_R.ReferenceP,w))
    c(E_Op.ColumnCountReferencePDeltaAdd,    ("pointer", "column_n_per_chunk", "subtract_one_f"),
                                              (E_R.Column,r+w), (0,r), (E_R.ReferenceP,r))
    c(E_Op.LineCountAdd,                     ("value",),
                                              (E_R.Line,r+w))
    #
    c(E_Op.PathIteratorSet,                  ("path_walker_id", "path_id", "offset"),
                                              (E_R.PathIterator,w))
    c(E_Op.RouterByLastAcceptance,           RouterContent, 
                                              (E_R.AcceptanceRegister,r), (E_R.InputP,w), (E_R.ThreadOfControl,w))
    c(E_Op.RouterOnStateKey,                 RouterOnStateKeyContent, 
                                              (E_R.TemplateStateKey,r), (E_R.PathIterator,r), (E_R.ThreadOfControl,w))
    c(E_Op.TemplateStateKeySet,              ("state_key",),
                                              (E_R.TemplateStateKey,w))
    #
    c(E_Op.PrepareAfterReload,               ("on_success_door_id", "on_failure_door_id"),
                                              (E_R.TargetStateIndex,w), (E_R.TargetStateElseIndex,w))
    #
    c(E_Op.QuexDebug,                        ("string",), 
                                              (E_R.StandardOutput,w))
    c(E_Op.QuexAssertNoPassage,              None, 
                                              (E_R.StandardOutput,w), (E_R.ThreadOfControl, r+w))

    return access_db, content_db, brancher_set, cost_db

_access_db,    \
_content_db,   \
_brancher_set, \
_cost_db       = __configure()

class OpList(list):
    """OpList -- a list of commands -- Intend: 'tuple' => immutable.
    """
    def __init__(self, *CL):
        self.__enter_list(CL)

    def __enter_list(self, Other):
        for op in Other:
            assert isinstance(op, Op), "%s: %s" % (op.__class__, op)
        super(OpList, self).__init__(Other)

    @classmethod
    def from_iterable(cls, Iterable):
        result = OpList()
        result.__enter_list(list(Iterable))
        return result

    def concatinate(self, Other):
        """Generate a mew OpList with .cloned() elements out of self and
        the Other OpList.
        """ 
        result = OpList()
        result.__enter_list([ x.clone() for x in self ] + [ x.clone() for x in Other ])
        return result

    def cut(self, NoneOfThis):
        """Delete all commands of NoneOfThis from this command list.
        """
        return OpList.from_iterable(
                           cmd for cmd in self if cmd not in NoneOfThis)

    def clone(self):
        return OpList.from_iterable(x.clone() for x in self)

    def is_empty(self):
        return super(OpList, self).__len__() == 0

    def cost(self):
        global _cost_db
        return sum(_cost_db[cmd.id] for cmd in self)

    def has_command_id(self, OpId):
        assert OpId in E_Op
        for cmd in self:
            if cmd.id == OpId: return True
        return False

    def access_accepter(self):
        """Gets the accepter from the command list. If there is no accepter
        yet, then it creates one and adds it to the list.
        """
        for cmd in self:
            if cmd.id == E_Op.Accepter: return cmd.content

        accepter = Op.Accepter()
        self.append(accepter)
        return accepter.content

    def replace_position_registers(self, PositionRegisterMap):
        """Replace for any position register indices 'x' and 'y' given by
         
                      y = PositionRegisterMap[x]

        replace register index 'x' by 'y'.
        """
        if PositionRegisterMap is None or len(PositionRegisterMap) == 0: 
            return

        for i in xrange(len(self)):
            cmd = self[i]
            if cmd.id == E_Op.StoreInputPosition:
                # Commands are immutable, so create a new one.
                new_command = Op.StoreInputPosition(cmd.content.pre_context_id, 
                                                 PositionRegisterMap[cmd.content.position_register],
                                                 cmd.content.offset)
                self[i] = new_command
            elif cmd.id == E_Op.IfPreContextSetPositionAndGoto:
                cmd.content.router_element.replace(PositionRegisterMap)
            elif cmd.id == E_Op.RouterByLastAcceptance:
                cmd.content.replace(PositionRegisterMap)

    def delete_superfluous_commands(self):
        """
        (1) A position storage which is unconditional makes any conditional
            storage superfluous. Those may be deleted without loss.
        (2) A position storage does not have to appear twice, leave the first!
            (This may occur due to register set optimization!)
        """
        for cmd in self:
            assert isinstance(cmd, Op), "%s" % cmd

        # (1) Unconditional rules out conditional
        unconditional_position_register_set = set(
            cmd.content.position_register
            for cmd in self \
                if     cmd.id == E_Op.StoreInputPosition \
                   and cmd.content.pre_context_id == E_PreContextIDs.NONE
        )
        delete_if(self,
                  lambda cmd:
                       cmd.id == E_Op.StoreInputPosition \
                   and cmd.content.position_register in unconditional_position_register_set \
                   and cmd.content.pre_context_id != E_PreContextIDs.NONE)

        # (2) Storage command does not appear twice. Keep first.
        #     (May occur due to optimizations!)
        occured_set = set()
        size        = len(self)
        i           = 0
        while i < size:
            cmd = self[i]
            if cmd.id == E_Op.StoreInputPosition: 
                if cmd not in occured_set: 
                    occured_set.add(cmd)
                else:
                    del self[i]
                    size -= 1
                    continue
            i += 1
        return

    def __hash__(self):
        xor_sum = 0
        for cmd in self:
            xor_sum ^= hash(cmd)
        return xor_sum

    def __eq__(self, Other):
        if isinstance(Other, OpList) == False: return False
        return super(OpList, self).__eq__(Other)

    def __ne__(self, Other):
        return not (self == Other)

    def __str__(self):
        return "".join("%s\n" % str(cmd) for cmd in self)

