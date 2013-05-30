from   quex.blackboard          import setup as Setup, \
                                       E_StateIndices, E_PreContextIDs, E_TriggerIDs
from   quex.engine.misc.file_in import error_msg
from   quex.engine.tools        import pair_combinations, TypedSet

from   collections              import defaultdict, namedtuple
from   operator                 import attrgetter, itemgetter
from   copy                     import deepcopy, copy
from   itertools                import islice, izip

class TransitionAction(object):
    """.transition_id --> information from what state the transition happens
                          and to what state it goes. if the trigger id is set
                          different triggers for the same transition may be
                          distinguished.
       .command_list  --> list of commands to be executed upon the transition.
       .door_id       --> An 'id' which is supposed to be unique for a command 
                          list. It tells 'where' a state is to be entered in 
                          order for the commands to be executed.
    """
    __slots__ = ("door_id", "command_list")
    def __init__(self, TheCommandList=None):
        assert TheCommandList is None or isinstance(TheCommandList, CommandList)

        self.door_id  = None # DoorID into door tree from where the command list is executed

        if TheCommandList is not None: self.command_list = TheCommandList
        else:                          self.command_list = CommandList()
 
    def clone(self):
        return TransitionAction(self.command_list.clone())

    # Make TransitionAction usable for dictionary and set
    def __hash__(self):      
        return hash(self.command_list)

    def __eq__(self, Other):
        return self.command_list == Other.command_list

    def __repr__(self):
        return "(%s: [%s])" % (self.door_id, self.command_list)

class TransitionID(object):
    """An 'advanced' implementation of a 'transition_id' that includes
       the state which is entered. Objects of this type can be used whenever
       a 'transition_id' is required with which an command_list is associated.

        state_index      --> target of the transition
        from_state_index --> origin of the transition
        trigger_id       --> if there are multiple transitions from 'from_state_index'
                             to 'state_index' with DIFFERENT command lists, then 
                             the transitions can be identified by a trigger-id.
                             

       Objects of this type are for example used in TemplateState objects.
    """
    __slots__ = ("state_index", "from_state_index", "trigger_id")
    def __init__(self, StateIndex, FromStateIndex, TriggerId=E_TriggerIDs.NONE):
        assert isinstance(StateIndex, (int, long))     or StateIndex     in E_StateIndices
        assert isinstance(FromStateIndex, (int, long)) or FromStateIndex in E_StateIndices
        assert isinstance(TriggerId, (int, long))      or TriggerId      in E_TriggerIDs
        self.state_index      = StateIndex
        self.from_state_index = FromStateIndex
        self.trigger_id       = TriggerId

    def precedes(self, Other):
        """This function helps sorting transition ids. It is not considered
           critical in the sense that it changes WHAT is going on. So, 
           the assumption that 'self' precedes 'Other' if both are equal
           does not do any harm. It safes some time, though at the place
           where this function is used (see  get_best_common_command_list()).
        """
        if   self.from_state_index < Other.from_state_index: return True
        elif self.from_state_index > Other.from_state_index: return False
        elif self.state_index < Other.state_index:           return True
        elif self.state_index > Other.state_index:           return False
        elif self.trigger_id < Other.trigger_id:                     return True
        elif self.trigger_id > Other.trigger_id:                     return False
        else:                                                return True 

    def __hash__(self):
        if isinstance(self.from_state_index, (int, long)): xor_sum = self.from_state_index + 1
        else:                                              xor_sum = 0
        if isinstance(self.state_index, (int, long)):      xor_sum ^= self.state_index + 1
        if isinstance(self.trigger_id, (int, long)):       xor_sum ^= self.trigger_id + 1
        return xor_sum

    def __eq__(self, Other):
        if not isinstance(Other, TransitionID): return False
        return     self.from_state_index == Other.from_state_index \
               and self.state_index      == Other.state_index \
               and self.trigger_id           == Other.trigger_id
    def __repr__(self):
        return "TransitionID(to=%s, from=%s)" % (self.state_index, self.from_state_index)

class Command(object):
    def __init__(self, Cost=None, ParamaterList=None, Hash=None):
        assert ParamaterList is None or type(ParamaterList) == list
        assert Hash is None          or isinstance(Hash, (int, long))
        self._cost = Cost
        self._hash = Hash
        self._x    = ParamaterList

    def clone(self):         
        if   self._x is None:   return self.__class__()
        elif len(self._x) == 1: return self.__class__(self._x[0])
        elif len(self._x) == 2: return self.__class__(self._x[0], self._x[1])
        elif len(self._x) == 3: return self.__class__(self._x[0], self._x[1], self._x[2])
        else:                   assert False

    def cost(self):          
        assert self._cost is not None, \
               "Derived class must implement .cost() function."
        return self._cost

    def __hash__(self):      
        if self._hash is not None:
            assert isinstance(self._hash, (int, long))
            return self._hash
        elif self._x is None:
            assert self._hash is not None, \
                   "Derived class must implement .__hash__() function."
            assert isinstance(self._hash, (int, long))
            return self._hash
        else:
            value = self._x[0]
            if isinstance(value, (int, long)): return value
            else:                              return -1

    def __eq__(self, Other): 
        if self.__class__ != Other.__class__:
            return False
        return self._x == Other._x

class CommandList:
    def __init__(self):
        self.accepter = None
        self.misc     = TypedSet(Command)

    @classmethod
    def from_iterable(cls, Iterable):
        result = CommandList()
        for cmd in Iterable:
            assert isinstance(cmd, Command)
            if isinstance(cmd, Accepter):
                assert self.accepter is None
                result.accepter = cmd
            else:
                result.misc.add(cmd)
        return result

    @staticmethod
    def intersection(This, That):
        result = CommandList()
        if This.accepter == That.accepter: result.accepter = This.accepter.clone()
        else:                              result.accepter = None
        result.misc = set(cmd.clone() for cmd in This.misc if cmd in That.misc)
        return result

    def clone(self):
        result = CommandList()
        if self.accepter is not None: result.accepter = self.accepter.clone()
        else:                         result.accepter = None
        result.misc = set(cmd.clone() for cmd in self.misc)
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

    def delete_SetPathIterator_commands(self):
        """Delete the 'SetPathIterator' command from the command list. There should
           never be more than ONE such command in a commant list. This is so, because
           the 'SetPathIterator' defines a state that the MegaState shall represent.
           A MegaState can only represent on state at a time.
        """
        for element in self.misc:
            if not isinstance(element, SetPathIterator): continue

            self.misc.remove(element)
            # Double check that there was only one SetPathIterator command in the list.
            for element in self.misc:
                assert not isinstance(element, SetPathIterator)

        return

    def __iter__(self):
        """Allow iteration over comand list."""
        if self.accepter is not None: 
            yield self.accepter
        def sort_key(Cmd):
            if   isinstance(Cmd, StoreInputPosition): 
                return (0, Cmd.pre_context_id, Cmd.position_register, Cmd.offset)
            elif isinstance(Cmd, PreConditionOK):   
                return (1, Cmd.pre_context_id)
            elif isinstance(Cmd, SetTemplateStateKey):   
                return (2, Cmd.value)
            elif isinstance(Cmd, SetPathIterator):   
                return (3, Cmd.offset, Cmd.path_id, Cmd.path_walker_id)
            else:
                assert False, "Command '%s' cannot be part of .misc." % Cmd.__class__.__name__

        for action in sorted(self.misc, key=sort_key):
            yield action

    def __hash__(self):
        xor_sum = 0
        for x in self.misc:
            xor_sum ^= hash(x)

        if self.accepter is not None:
            xor_sum ^= hash(self.accepter)

        return xor_sum

    def is_equivalent(self, Other):
        """For 'equivalence' the commands 'MegaState_Command' are unimportant."""
        # Rely on '__eq__' of Accepter
        if not (self.accepter == Other.accepter): return False
        self_misc_pure  = set(cmd for cmd in self.misc  if not isinstance(cmd, MegaState_Command))
        Other_misc_pure = set(cmd for cmd in Other.misc if not isinstance(cmd, MegaState_Command))
        return self_misc_pure == Other_misc_pure

    def __eq__(self, Other):
        # Rely on '__eq__' of Accepter
        if not (self.accepter == Other.accepter): return False
        return self.misc == Other.misc

    def __repr__(self):
        txt = ""
        if self.accepter is not None:
            txt += "a"
            for x in self.accepter:
                txt += "%s," % repr(x.pattern_id)

        for action in self.misc:
            txt += "%s" % action
        return txt

class IncrementInputP(Command):
    def __init__(self):  
        Command.__init__(self, 1, Hash=0x4711)

class BeforeIncrementInputP_Command(Command):
    """Base class for all commands which have to appear BEFORE
       the input pointer increment action.
    """
    pass

class CountColumnN_ReferenceSet(BeforeIncrementInputP_Command):
    def __init__(self):  
        Command.__init__(self, 1, Hash=0x4712)

class CountColumnN_ReferenceAdd(BeforeIncrementInputP_Command):
    def __init__(self, ColumnNPerChunk):      
        Command.__init__(self, 1, [ColumnNPerChunk])
    @property
    def column_n_per_chunk(self): 
        return self._x[0]

class CountColumnN_Add(Command):
    def __init__(self, Offset):      
        Command.__init__(self, 1, [Offset])
    @property
    def offset(self): 
        return self._x[0]

class CountColumnN_Grid(BeforeIncrementInputP_Command):
    def __init__(self, GridWidth):      
        Command.__init__(self, 1, [GridWidth])
    @property
    def grid_width(self): 
        return self._x[0]

class CountLineN_Add(Command):
    def __init__(self, Offset):      
        Command.__init__(self, 1, [Offset])
    @property
    def offset(self): 
        return self._x[0]

class StoreInputPosition(BeforeIncrementInputP_Command):
    """
    StoreInputPosition: 

    Storing the input position is actually dependent on the pre_context_id, if 
    there is one. The pre_context_id is left out for the following reasons:

    -- Testing the pre_context_id is not necessary.
       If a pre-contexted acceptance is reach where the pre-context is required
       two things can happen: 
       (i) Pre-context-id is not fulfilled, then no input position needs to 
           be restored. Storing does no harm.
       (ii) Pre-context-id is fulfilled, then the position is restored. 

    -- Avoiding overhead for pre_context_id test.
       In case (i) cost = test + jump, (ii) cost = test + assign + jump. Without
       test (i) cost = assign, (ii) cost = storage. Assume cost for test <= assign.
       Thus not testing is cheaper.

    -- In the process of register economization, some post contexts may use the
       same position register. The actions which can be combined then can be 
       easily detected, if no pre-context is considered.
    """
    def __init__(self, PreContextID, PositionRegister, Offset):
        Command.__init__(self, 1, [PreContextID, PositionRegister, Offset])

    def GET_pre_context_id(self):       return self._x[0]
    def SET_pre_context_id(self, X):    self._x[0] = X
    pre_context_id = property(GET_pre_context_id, SET_pre_context_id)
    def GET_position_register(self):    return self._x[1]
    def SET_position_register(self, X): self._x[1] = X
    position_register = property(GET_position_register, SET_position_register)
    def GET_offset(self):               return self._x[2]
    def SET_offset(self, X):            self._x[2] = X
    offset = property(GET_offset, SET_offset)

    def __hash__(self):
        # 'Command.__hash__' takes '_x[0]' as hash value.
        # position_register = _x[1]
        if isinstance(self.position_register, (int, long)): return self.position_register
        else:                                               return -1

    def __cmp__(self, Other):
        if   self.pre_context_id    > Other.pre_context_id:    return 1
        elif self.pre_context_id    < Other.pre_context_id:    return -1
        elif self.position_register > Other.position_register: return 1
        elif self.position_register < Other.position_register: return -1
        elif self.offset            > Other.offset:            return 1
        elif self.offset            < Other.offset:            return -1
        return 0

    def __repr__(self):
        # if self.pre_context_id != E_PreContextIDs.NONE:
        #     if_txt = "if '%s': " % repr_pre_context_id(self.pre_context_id)
        # else:
        #     if_txt = ""
        #
        # if self.offset == 0:
        #     return "%s%s = input_p;\n" % (if_txt, repr_position_register(self.position_register))
        # else:
        #     return "%s%s = input_p - %i;\n" % (if_txt, repr_position_register(self.position_register), 
        #                                        self.offset))
        return "pre(%s) --> store[%i] = input_p - %i;\n" % \
               (self.pre_context_id, self.position_register, self.offset) 

class PreConditionOK(Command):
    def __init__(self, PreContextID):
        Command.__init__(self, 1, [PreContextID])
    @property
    def pre_context_id(self): return self._x[0]
    def __repr__(self):       
        return "    pre-context-fulfilled = %s;\n" % self.pre_context_id

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

class MegaState_Command(Command):
    """Base class for all commands related to MegaState control, 
       such as 'SetTemplateStateKey' and 'SetPathIterator'.
    """
    pass

class SetTemplateStateKey(MegaState_Command):
    def __init__(self, StateKey):
        Command.__init__(self, 1, [StateKey])
    @property
    def value(self): return self._x[0]
    def set_value(self, Value): 
        assert isinstance(Value, (int, long))
        self._x[0] = Value
    def __repr__(self):       
        return "    state_key = %s;\n" % self.value

class SetPathIterator(MegaState_Command):
    def __init__(self, Offset, PathWalkerID=-1, PathID=-1):
        Command.__init__(self, 1, [Offset, PathWalkerID, PathID])

    def set_path_walker_id(self, Value): self._x[1] = Value
    def set_path_id(self, Value):        self._x[2] = Value

    @property
    def offset(self):         return self._x[0]
    @property
    def path_walker_id(self): return self._x[1]
    @property
    def path_id(self):        return self._x[2]

    def __hash__(self):       
        return self.path_walker_id ^ self.path_id ^ self.offset

    def __repr__(self):       
        return "    (pw=%s,pid=%s,off=%s)\n" % (self.path_walker_id, self.path_id, self.offset)

class DoorID(object):
    __slots__ = ("__state_index", "__door_index")
    def __init__(self, StateIndex, DoorIndex):
        assert isinstance(StateIndex, (int, long)) or StateIndex in E_StateIndices
        # 'DoorIndex is None' --> right after the entry commands (targetted after reload).
        assert isinstance(DoorIndex, (int, long))  or DoorIndex is None
        self.__state_index = StateIndex
        self.__door_index  = DoorIndex
    @property
    def state_index(self): return self.__state_index
    @property
    def door_index(self): return self.__door_index
    def set_door_index(self, Value): self.__door_index = Value

    def set(self, Other):
        self.__state_index = Other.__state_index
        self.__door_index  = Other.__door_index

    def clone(self):
        return DoorID(self.__state_index, self.__door_index)
    def __hash__(self):
        if isinstance(self.__state_index, (int, long)): xor_sum = self.__state_index + 1
        else:                                           xor_sum = 0
        xor_sum ^= self.__door_index 
        return xor_sum
    def __eq__(self, Other):
        if not isinstance(Other, DoorID): return False
        return     self.__state_index == Other.__state_index \
               and self.__door_index  == Other.__door_index
    def __cmp__(self, Other):
        if not isinstance(Other, DoorID): return -1
        result = cmp(self.__state_index, Other.__state_index)
        if result != 0: return result
        return cmp(self.__door_index, Other.__door_index)
    def __repr__(self):
        return "DoorID(s=%s, d=%s)" % (self.__state_index, self.__door_index)

