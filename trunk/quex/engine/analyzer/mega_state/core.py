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

    def map_state_key_to_state_index(self, StateKey):
        assert False, "This function needs to be overwritten by derived class."

class PseudoMegaState(MegaState):
    """A pseudo mega state is a state that represent a single AnalyzerState
       but acts as it was a real 'MegaState'. That means:

          -- .transition_map:  maps   interval --> MegaState_Target

             and not interval to target state.
    """
    def __init__(self, Represented_AnalyzerState):
        assert not isinstance(Represented_AnalyzerState, MegaState)
        self.__state = Represented_AnalyzerState
        MegaState.__init__(self, StateIndex=Represented_AnalyzerState.index)

        self.__state_index_list = [ Represented_AnalyzerState.index ]

        self.transition_map     = self.__transition_map_construct()

    def __transition_map_construct(self):
        """Build a transition map that triggers to MegaState_Target-s rather
           than simply to target states.

           CAVEAT: In general, it is **NOT TRUE** that if two transitions (x,a)
           and (x, b) to a state 'x' share a DoorID in the original state, then
           they share the DoorID in the MegaState. 
           
           The critical case is the recursive transition (x,x). It may trigger
           the same actions as another transition (x,a) in the original state.
           However, when 'x' is implemented in a MegaState it needs to set a
           'state_key' upon entry from 'a'. This is, or may be, necessary to
           tell the MegaState on which's behalf it has to operate. The
           recursive transition from 'x' to 'x', though, does not have to set
           the state_key, since the MegaState still operates on behalf of the
           same state. While (x,x) and (x,a) have the same DoorID in the
           original state, their DoorID differs in the MegaState which
           implements 'x'.

           THUS: A translation 'old DoorID' --> 'new DoorID' is not sufficient
           to adapt transition maps!

           Here, the recursive target is implemented as a 'scheme' in order to
           prevent that it may be treated as 'uniform' with other targets.
        """

        def get(Target, SelfIndex):
            if Target == SelfIndex: return MegaState_Target.create((Target,))
            else:                   return MegaState_Target.create(Target)

        return [ (interval, get(target, self.index)) \
                 for interval, target in self.__state.transition_map]

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

    def map_state_key_to_state_index(self, StateKey):
        assert False, "PseudoMegaState-s exist only for analysis. They shall never be implemented."

class AbsorbedState_Entry(Entry):
    def __init__(self, StateIndex, TransitionDB, DoorDB):
        """Map: Transition --> DoorID of the implementing state.
        """
        Entry.__init__(self, StateIndex, FromStateIndexList=[])
        self.set_transition_db(TransitionDB)
        self.set_door_db(DoorDB)

class AbsorbedState(AnalyzerState):
    """An AbsorbedState object represents an AnalyzerState which has
       been implemented by a MegaState. Its sole purpose is to pinpoint
       to the MegaState which implements it and to translate the transtions
       into itself to DoorIDs into the MegaState.
    """
    def __init__(self, AbsorbedAnalyzerState, AbsorbingMegaState):
        AnalyzerState.set_index(self, AbsorbedAnalyzerState.index)
        # The absorbing MegaState may, most likely, contain other transitions
        # than the transitions into the AbsorbedAnalyzerState. Those, others
        # do not do any harm, though. Filtering out those out of the hash map
        # does, most likely, not bring any benefit.
        self.entry       = AbsorbedState_Entry(AbsorbedAnalyzerState.index, 
                                               AbsorbingMegaState.entry.transition_db,
                                               AbsorbingMegaState.entry.door_db)
        self.absorbed_by = AbsorbingMegaState
        self.__state     = AbsorbedAnalyzerState

    @property
    def drop_out(self):
        return self.__state.drop_out

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
    __slots__ = ('__scheme', '__drop_out_f', '__target_state_index', 'code')

    __object_db = dict()

    @staticmethod
    def init():
        """Initializes: '__object_db' which keeps track of generated MegaState_Target-s."""
        MegaState_Target.__object_db.clear()
        # The Drop-Out target must be always in there.
        MegaState_Target.__object_db[E_StateIndices.DROP_OUT] = MegaState_Target_DROP_OUT

    @staticmethod
    def disconnect_object_db():
        """Disconnects the '__object_db' so that it may be used without influencing 
           the '__object_db' of MegaState_Target.
        """
        tmp_object_db                = MegaState_Target.__object_db
        MegaState_Target.__object_db = dict()
        return tmp_object_db

    @staticmethod
    def create(Target):
        assert Target is not None 

        result = MegaState_Target.__object_db.get(Target)
        if result is None: 
            result = MegaState_Target(Target)
            MegaState_Target.__object_db[Target] = result

        return result

    def __init__(self, Target):
        if Target is None: # Only to be used by 'self.clone()'
            return 

        self.__drop_out_f         = False
        self.__target_state_index = None
        self.__scheme             = None

        if   Target == E_StateIndices.DROP_OUT: self.__drop_out_f         = True   
        elif isinstance(Target, long):          self.__target_state_index = Target 
        elif isinstance(Target, tuple):         self.__scheme             = Target
        else:                                   assert False, Target.__class__.__name__

    def clone(self):
        assert False # Why cloning?
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
        elif self.scheme  is not None:            return "MegaState_Target:scheme(%s)" % repr(self.__scheme).replace("L", "")
        else:                                     return "MegaState_Target:<ERROR>"

    def __hash__(self):
        if   self.__drop_out_f:                     return 0
        elif self.__target_state_index is not None: return self.__target_state_index.state_index
        elif self.__scheme is not None:             return hash(self.__scheme)
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


