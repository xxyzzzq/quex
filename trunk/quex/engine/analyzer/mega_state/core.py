import quex.engine.state_machine.index               as     index
from   quex.engine.analyzer.state.core               import AnalyzerState
from   quex.engine.analyzer.state.entry              import Entry
from   quex.engine.analyzer.state.entry_action       import DoorID
from   quex.blackboard                               import E_StateIndices

from itertools import chain
from copy      import copy, deepcopy

class MegaState_Entry(Entry):
    def __init__(self, MegaStateIndex):
        Entry.__init__(self, MegaStateIndex, FromStateIndexList=[])

class MegaState(AnalyzerState):
    """A MegaState is a state that implements more than one state at once.
       Examples are 'TemplateState' and 'PathwalkerState'.
    """
    def __init__(self, StateIndex=None):
        assert StateIndex is None or isinstance(StateIndex, long)
        if StateIndex is None: StateIndex = index.get()
        AnalyzerState.set_index(self, StateIndex)

        self.__door_id_replacement_db = None

    @property
    def init_state_f(self): return False

    def implemented_state_index_list(self):
        assert False, "This function needs to be overwritten by derived class."

    def map_state_index_to_state_key(self, StateIndex):
        assert False, "This function needs to be overwritten by derived class."

class PseudoMegaState(MegaState):
    """A pseudo mega state is a state that represent a single AnalyzerState
       but acts as it was a real 'MegaState'. This means:

          -- transition_map:  interval --> DoorID

             and not interval to target state.
    """
    def __init__(self, Represented_AnalyzerState):
        self.__state       = Represented_AnalyzerState
        MegaState.__init__(self, StateIndex=Represented_AnalyzerState.index)

        self.__state_index_list = [ Represented_AnalyzerState.index ]

    def transition_map_construct(self, StateDB):
        self.transition_map = [(interval, MegaState_Target.create(target)) \
                               for interval, target in self.__state.transition_map ]

    @property
    def entry(self):
        return self.__state.entry

    @property
    def drop_out(self):
        return self.__state.drop_out

    @property
    def state_index_list(self):
        return self.__state_index_list

    def implemented_state_index_list(self):
        return self.__state_index_list

    def map_state_index_to_state_key(self, StateIndex):
        assert False, "PseudoMegaState-s exist only for analysis. They shall never be implemented."

class AbsorbedState_Entry:
    def __init__(self, TransitionDB):
        """Map: Transition --> DoorID of the implementing state.
        """
        self.transition_db = TransitionDB

class AbsorbedState(AnalyzerState):
    """An AbsorbedState object represents an AnalyzerState which has
       been implemented by a MegaState. Its sole purpose is to pinpoint
       to the MegaState which implements it and to translate the transtions
       into itself to DoorIDs into the MegaState.
    """
    def __init__(self, AbsorbedAnalyzerState, AbsorbingMegaState, TransitionDB)
        AnalyzerState.set_index(self, AbsorbedAnalyzerState.index)
        # The absorbing MegaState may, most likely, contain other transitions
        # than the transitions into the AbsorbedAnalyzerState. Those, others
        # do not do any harm, though. Filtering out those out of the hash map
        # does, most likely, not bring any benefit.
        self.entry       = ImplementedState_Entry(AbsorbingMegaState.entry.transition_db)
        self.absorbed_by = AbsorbingMegaState

class MegaState_Target(object):
    """A mega state target contains the information about what the target
       state is for a given interval for a given template key. For example,
       a given interval X triggers to target scheme T, i.e. there is an
       element in the transition map:

                ...
                [ X, T ]
                ...

       then 'T.scheme[key]' tells the 'target state index' for a given state
       key. The door through which it enters is determined by the transition

           TransitionID(FromStateIndex = state associated with 'key', 
                        ToStateIndex   = T.scheme[key])

       Which can be translated into a DoorID by the target state's entry
       database 'transition_db'.
       
       There might be multiple intervals following the same target scheme,
       so the function 'TargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TargetSchemeDB.get()'. It helps
                     later to define the scheme only once, even it appears
                     twice or more.
    """
    __slots__ = ('__index', '__scheme', '__drop_out_f', '__target_state_index', '__scheme')

    @staticmethod
    def create(Target, UniqueIndex=None):
        assert Target is not None # Only to be used by 'self.clone()'

        if Target == E_StateIndices.DROP_OUT:  return MegaState_Target_DROP_OUT
        return MegaState_Target(Target, UniqueIndex)

    def __init__(self, Target, UniqueIndex=None):
        if Target is None: # Only to be used by 'self.clone()'
            return 

        if UniqueIndex is not None: 
            assert isinstance(Target, tuple)
        else:
            assert isinstance(Target, long) or Target == E_StateIndices.DROP_OUT 

        self.__index = UniqueIndex
        self.__drop_out_f         = False
        self.__target_state_index = None
        self.__scheme             = None

        if   Target == E_StateIndices.DROP_OUT: self.__drop_out_f         = True;   assert UniqueIndex is None
        elif isinstance(Target, long):          self.__target_state_index = Target; assert UniqueIndex is None
        elif isinstance(Target, tuple):         self.__scheme             = Target; assert UniqueIndex is not None
        else:                                   assert False

    def clone(self):
        if self.__drop_out_f: return self 

        result = MegaState_Target(Target=None) 
        result.__drop_out_f = False
        result.__index      = self.__index
        result.__target_state_index = self.__target_state_index
        if self.__scheme is None: result.__scheme = None
        else:                     result.__scheme = copy(self.__scheme) # Shallow copy sufficient for numbers
        return result

    @property
    def scheme(self):              return self.__scheme
    @property
    def target_state_index(self):  return self.__target_state_index
    @property
    def drop_out_f(self):          return self.__drop_out_f
    @property
    def index(self):               return self.__index

    def __repr__(self):
        if   self.drop_out_f:                     return "MegaState_Target:DropOut"
        elif self.target_state_index is not None: return "MegaState_Target:(%s)"       % repr(self.__target_state_index)
        elif self.scheme  is not None:            return "MegaState_Target:scheme(%s)" % repr(self.__scheme)
        else:                                     return "MegaState_Target:<ERROR>"

    def __hash__(self):
        if   self.__drop_out_f:                     return 0
        elif self.__target_state_index is not None: return self.__target_state_index.state_index
        elif self.__scheme is not None:             return self.__scheme[0].state_index
        else:                                       assert False

    def __eq__(self, Other):
        if   isinstance(Other, MegaState_Target) == False: 
            return False
        elif self.__drop_out_f and Other.__drop_out_f: 
            return True
        elif self.__target_state_index is not None and Other.__target_state_index is not None:
            return self.__target_state_index == Other.__target_state_index
        elif self.__scheme  is not None and Other.__scheme  is not None:
            return self.__scheme == Other.__scheme
        else:
            return False
        ## if self.__index != Other.__index: return False
        return self.__scheme == Other.__scheme

# Globally unique object to stand up for all 'drop-outs'.
MegaState_Target_DROP_OUT = MegaState_Target(E_StateIndices.DROP_OUT)

class MegaState_DropOut(dict):
    """Map: 'DropOut' object --> indices of states that implement the 
                                 same drop out actions.

       For example, if four states 1, 4, 7, and 9 have the same drop_out 
       behavior DropOut_X, then this is stated by an entry in the dictionary as

             { ...     DropOut_X: [1, 4, 7, 9],      ... }

       For this to work, the drop-out objects must support a proper interaction
       with the 'dict'-objects. Namely, they must support:

             __hash__          --> get the right 'bucket'.
             __eq__ or __cmp__ --> compare elements of 'bucket'.
    """
    def __init__(self, *StateList):
        for state in StateList:
            self.update_from_state(state)
        return

    @property
    def uniform_f(self):
        """Uniform drop-out means, that for all drop-outs mentioned the same
           actions have to be performed. This is the case, if all states are
           categorized under the same drop-out. Thus the dictionary's size
           will be '1'.
        """
        return len(self) == 1

    def is_uniform_with(self, Other):
        """The given Other drop-out belongs to a 'normal state'. This function
           investigates if it's drop-out behavior is the same as all in others
           in this MegaState_DropOut. 

           If this MegaState_DropOut is not uniform, then of course it cannot
           become uniform with 'Other'.
        """
        if not self.uniform_f: return False

        prototype = self.iterkeys().next()
        return prototype == Other

    def update_from_other(self, MS_DropOut):
        for drop_out, state_index_set in MS_DropOut.iteritems():
            # assert hasattr(drop_out, "__hash__")
            # assert hasattr(drop_out, "__eq__") # PathWalker may enter 'None' in unit test
            x = self.get(drop_out)
            if x is None: self[drop_out] = copy(state_index_set)
            else:         x.update(state_index_set)

    def update_from_state(self, TheState):
        drop_out = TheState.drop_out
        if hasattr(drop_out, "iteritems"): 
            self.update_from_other(drop_out)
            return
        #assert hasattr(drop_out, "__hash__")
        #assert hasattr(drop_out, "__eq__")
        x = self.get(drop_out)
        if x is None: self[drop_out] = set([TheState.index])
        else:         x.add(TheState.index)

def get_state_list(X): 
    if hasattr(X, "state_index_list"): return X.state_index_list 
    else:                              return [ X.index ]

def get_iterable(X, StateIndexList): 
    if hasattr(X, "iteritems"): return X.iteritems()
    else:                       return [(X, StateIndexList)]


