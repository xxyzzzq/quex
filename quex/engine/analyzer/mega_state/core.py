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
        self.__door_id_replacement_db = None

    @property
    def door_id_replacement_db(self):
        """The MegaState implements a set of states. The entry doors of these
           states are implemented in the MegaState_Entry. This property
           returns a dictionary that maps from doors of original states to
           doors of this MegaState which implement these doors.

           door_db:  transition_id(x, y) --> door_id_z(si, di)

           Documents that the transition into state 'x' from state 'y' is 
           implemented by door 'door_id_z(si, di)' determined by the 
           state index 'si' of the implementing state and the door index 'di'
           pointing into the state's door tree. 

           Now, that the state is implemented by a MegaState, the transition
           must be associated with a DoorID from the MegateState. This documents
           that the MegaState implements this transition.

           The translation from old DoorID to new DoorID happens by means of the
           transition_ids which remain the same.
        """
        assert self.__door_id_replacement_db is not None, \
               ".door_tree_configure(StateDB, ImplementedStateIndexList) must be called before."
        return self.__door_id_replacement_db

    def door_tree_configure(self, StateDB, ImplementedStateIndexList):
        """First: See 'Entry.door_tree_configure()'. 
        
           This overwriting function extends the base's .door_tree_configure()
           by alse providing the '__door_id_replacement_db'. 
           
           A MegaState implements more than one state. Therefore, it directs
           transitions into normal states into its own doors. Namely, the
           TransitionID-s that originaly were associated with DoorID-s of an
           AnalyzerState are now associated with DoorID-s of the MegaState.
            
           The base class' .door_tree_configure() translates the 'action_db'
           into a door tree and provides the 'door_db' and the 'transition_db';
           where the used DoorID-s now relate to the MegaState. Using the 
           TransitionID keys from 'transition_db' allows to get the DoorID 
           from the AnalyzerState's 'door_db'.
        """
        # Based on the now existing 'action_db' the door tree can be
        # configured. Also, it results the 'door_db' and the 'transition_db'.
        Entry.door_tree_configure(self)

        # Derive the replacement database.
        result = {}
        for state_index in ImplementedStateIndexList:
            # map: TransitionID-s of AnalyzerState --> DoorID-s of MegaState.
            transition_db = StateDB[state_index].entry.transition_db
            for door_id, transition_id_list in transition_db.iteritems():
                if len(transition_id_list) == 0:
                    # Only one DoorID can possibly be associated with no TransitionID: 
                    # The root of the door tree. Its index is 0. Since no transition
                    # happens through this door, it does not need to be mentioned.
                    assert door_id.door_index == 0
                    continue

                # All TransitionID-s of a door are associate with the same commands.
                # => They must enter through the same door in the MegaState. 
                # => Considering any one TransitionID from the list is enough.
                transition_id = transition_id_list[0] # Take any transition
                new_door_id   = self.door_db.get(transition_id)
                # The transition may have been deleted, for example, because it lies
                # on the path of a uniform path walker.
                if new_door_id is None: continue 

                result[door_id] = new_door_id

        self.__door_id_replacement_db = result

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

    def replace_door_ids_in_transition_map(self, ReplacementDB):
        """ReplacementDB:    DoorID --> Replacement DoorID

           The Existence of MegaStates has the consequence that transitions
           have to be adapted. Let 'X' be a state that has been absorbed by 
           a MegaState 'M'. Then a transition from another state 'Y' to 'X' is 
           originally associated with DoorID 'Dyx'. Since 'X' is now part
           of a MegaState, the transition 'from Y to X' has been associated
           with the DoorID 'Dyxm' which is the MegaState's entry that represents
           'from Y to X'. Any transition 'Dyx' must now be replaced by 'Dyxm'.
        """
        for i, info in enumerate(self.transition_map):
            interval, target = info
            if target.drop_out_f: continue
            new_target = target.door_id_replacement(ReplacementDB)
            if new_target is not None:
                self.transition_map[i] = (interval, new_target)

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

        self.__entry_clone  = self.__entry_construct()
        self.__state_index_list = [ Represented_AnalyzerState.index ]

    def transition_map_construct(self, StateDB):
        def adapt(Target):
            if Target == E_StateIndices.DROP_OUT: 
                return MegaState_Target_DROP_OUT
            else:
                door_id = StateDB[Target].entry.get_door_id(Target, self.index)
                return MegaState_Target.create(door_id)

        self.transition_map = [(interval, adapt(target)) \
                               for interval, target in self.__state.transition_map ]
        if False and self.index == 79:
            StateA = self.__state
            print "##self.index:", self.index
            for key, value in self.entry.door_db.iteritems():
                print "##", key, value
            # print "##door tree:", self.entry.door_tree_root.get_string(self.__entry.transition_db)
            print "##transition_db:"
            for door_id, transition_id_list in self.__entry_clone.transition_db.iteritems():
                print "##", door_id, " --> ", transition_id_list
            print "##transition_map:"
            for interval, target in StateA.transition_map:
                print "##", target
            for interval, target in self.transition_map:
                print "##tm_a", target


    @property
    def entry(self):
        return self.__entry_clone

    @property
    def drop_out(self):
        return self.__state.drop_out

    def map_state_index_to_state_key(self, StateIndex):
        assert False, "PseudoMegaState-s exist only for analysis. They shall never be implemented."

    @property
    def state_index_list(self):
        return self.__state_index_list
    def implemented_state_index_list(self):
        return self.__state_index_list

    def __entry_construct(self):
        """Configure information about entry into the state. There is one special thing to 
           consider: The door of the recursive transition (from_state == to_state) must be
           different from the other doors. Later when the state is implemented in a MegaState,
           the recursive door does not need the state_key to be set, while all other transitions
           into the state require this. 

           The exact structure of the door tree is totally unimportant at this point in
           time.
        """
        result = deepcopy(self.__state.entry)

        # (*) Search for a recursive transition
        transition_db = result.transition_db
        door_db       = result.door_db
        for transition_id, door_id in door_db.iteritems():
            if transition_id.state_index != transition_id.from_state_index: continue
            break # We found the recursive transition in the state 
            #     # => Go and handle it.
        else:
            return result # (*) None found, no worry.

        # (*) The recurive transition 'transition_id'

        #  -- Check whether it has an isolated DoorID
        transition_id_list = transition_db[door_id]
        assert len(transition_id_list) > 0
        if len(transition_id_list) == 1: 
            assert transition_id_list[0] == transition_id
            return result # (*) Recursive transition is isolated from rest, no worry.

        # -- It shares the door with other transitions.
        # => Put the recursive transition into an extra door.
        #    Find the largest door_index => new door_index = max + 1
        max_door_id = max(x.door_index for x in transition_db.iterkeys())
        extra_door  = DoorID(door_id.state_index, max_door_id + 1)
        transition_db[extra_door] = [transition_id]
        door_db[transition_id]    = extra_door

        # -- Delete the recursive transition from 'transition_id_list'
        #    => This deletes its reference in 'door_db'
        del transition_id_list[transition_id_list.index(transition_id)]

        return result

class MegaState_Target(object):
    """A mega state target contains the information about what the target
       state is for a given interval for a given template key. For example,
       a given interval X triggers to target scheme T, i.e. there is an
       element in the transition map:

                ...
                [ X, T ]
                ...

       then 'T.scheme[key]' tells the 'door id' of the door into a state that
       is entered for the case the operates with the given 'key'. A key in
       turn, stands for a particular state.

       There might be multiple intervals following the same target scheme,
       so the function 'TargetSchemeDB.get()' takes care of making 
       those schemes unique.

           .scheme = Target state index scheme as explained above.

           .index  = Unique index of the target scheme. This value is 
                     determined by 'TargetSchemeDB.get()'. It helps
                     later to define the scheme only once, even it appears
                     twice or more.
    """
    __slots__ = ('__index', '__scheme', '__drop_out_f', '__door_id', '__scheme')

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
            assert isinstance(Target, DoorID) or Target == E_StateIndices.DROP_OUT 

        self.__index       = UniqueIndex

        self.__drop_out_f  = False
        self.__door_id     = None
        self.__scheme      = None

        if   Target == E_StateIndices.DROP_OUT:  self.__drop_out_f  = True;   assert UniqueIndex is None
        elif isinstance(Target, DoorID):         self.__door_id     = Target; assert UniqueIndex is None
        elif isinstance(Target, tuple):          self.__scheme      = Target; assert UniqueIndex is not None

    def clone(self):
        if self.__drop_out_f: return self 

        result = MegaState_Target(Target=None) 
        result.__drop_out_f = False
        result.__index      = self.__index
        if self.__door_id is None: result.__door_id = None
        else:                      result.__door_id = self.__door_id.clone()
        if self.__scheme is None:  result.__scheme  = None
        else:
            def __clone(X):
                if X == E_StateIndices.DROP_OUT: return X
                else:                            return X.clone()
            result.__scheme = tuple(__clone(x) for x in self.__scheme)
        return result

    @property
    def scheme(self):      return self.__scheme

    @property
    def door_id(self):     return self.__door_id

    def door_id_replacement(self, ReplacementDB):
        """RETURNS: 
             None    -- if ReplacementDB does not have any effect on the
                        MegaState_Target object.
             Object  -- if an adaption according to ReplacementDB had to 
                        occur. In this case, the MegaState_Target creates
                        a clone of itself, modifies it according to 
                        ReplacementDB and returns that clone.
        """
        if self.drop_out_f: 
            return # The whole target is not need to be modified!

        result  = self
        # If a door_id needs to be really adapted, then the Target needs to be
        # cloned, i.e. disconnected from its original. Thus changes to it wont
        # effect the original.
        if self.door_id is not None:  
            # (*) Target Uniform DoorID
            new_door_id = ReplacementDB.get(self.door_id)
            if new_door_id is not None: 
                result   = self.clone()     # disconnect from original
                result.door_id.set(new_door_id)
                return result
            return # No change to 'self'

        cloned_f = False
        for i, door_id in enumerate(result.scheme):
            new_door_id = ReplacementDB.get(door_id)
            if new_door_id is not None: 
                if not cloned_f: 
                    result   = result.clone() # Disconnect from original
                    cloned_f = True
                result.scheme[i].set(new_door_id)

        if not cloned_f: 
            return # The whole target does not need to be touched!

        return result

    @property
    def drop_out_f(self):  return self.__drop_out_f

    @property
    def index(self):       return self.__index

    def __repr__(self):
        if   self.drop_out_f:          return "MegaState_Target:DropOut"
        elif self.door_id is not None: return "MegaState_Target:(%s)" % repr(self.__door_id)
        elif self.scheme  is not None: return "MegaState_Target:scheme(%s)" % repr(self.__scheme)
        else:                          return "MegaState_Target:<ERROR>"

    def __hash__(self):
        if   self.__drop_out_f:          return 0
        elif self.__door_id is not None: return self.__door_id.state_index
        elif self.__scheme is not None:  return self.__scheme[0].state_index
        else:                            assert False

    def __eq__(self, Other):
        if   isinstance(Other, MegaState_Target) == False: 
            return False
        elif self.__drop_out_f and Other.__drop_out_f: 
            return True
        elif self.__door_id is not None and Other.__door_id is not None:
            return self.__door_id == Other.__door_id
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


