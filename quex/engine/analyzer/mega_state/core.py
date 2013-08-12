"""MEGA STATES _________________________________________________________________

A 'MegaState' is a state which absorbs and implements multiple AnalyzerState-s
in a manner that is beneficial in terms of code size, computational speed, or
both. All MegaState-s shall be derived from class MegaState, and thus are
committed to the described interface. The final product of a MegaState is a
piece of code which can act on behalf of its absorbed AnalyzerState-s. 

A 'state_key' indicates for any point in time the AnalyzerState which the
MegaState represents. 

The following scheme displays the general idea of a class hierarchy with a
MegaState involved. At the time of this writing there are two derived classes
'TemplateState' and 'PathWalkerState'--each represent a compression algorith: 

    AnalyzerState <------- MegaState <----+---- TemplateState
                                          |
                                          '---- PathWalkerState


Analogous to the AnalyzerState, a MegaState has special classes to implement
'Entry' and 'DropOut', namely 'MegaState_Entry' and 'MegaState_DropOut'.  Where
an AnalyzerState's transition_map associates a character interval with a target
state index, the MegaState's transition_map associates a character interval
with a 'MegaState_Transition'. Given a state_key, the MegaState_Transition provides the
target state index for the given character interval.

The following pinpoints the general idea of a MegaState.

    MegaStateEntry:
 
        ... entry doors of absorbed states ...

    /* Some Specific Actions ... */

    tansition_map( input ) {
        in interval_0:  MegaState_Target_0[state_key];  --> Target states
        in interval_1:  MegaState_Target_1[state_key];  --> depending on
        in interval_2:  MegaState_Target_2[state_key];  --> current input
        ...                                             --> character.
        in interval_N:  MegaState_Target_N[state_key]; 
    }

    MegaState_DropOut:

        ... drop-out actions of absorbed states ...
_______________________________________________________________________________

This file provides two special classes for to represent 'normal' 
AnalyzerState-s:

-- PseudoMegaState: represents an AnalyzerState as if it was a 
                    MegaState. This way, it may act homogeneously in 
                    algorithms that work on MegaState-s and AnalyzerState-s
                    at the same time.
 
-- AbsorbedState:   represent an AnalyzerState in the original state database,
                    even though it is absorbed by a MegaState.

_______________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
"""
from quex.engine.analyzer.state.core         import AnalyzerState
from quex.engine.analyzer.mega_state.target  import MegaState_Transition, \
                                                    MegaState_Target_DROP_OUT
from quex.engine.analyzer.state.entry        import Entry
from quex.engine.analyzer.state.drop_out     import DropOut, \
                                                    DropOutIndifferent, \
                                                    DropOutBackwardInputPositionDetection
from quex.engine.analyzer.state.entry_action import DoorID
from quex.engine.analyzer.transition_map     import TransitionMap
from quex.blackboard                         import E_StateIndices

from quex.engine.tools import print_callstack, \
                              TypedDict

from copy import copy

class DoorIdReassignmentDB(dict):
    def __init__(self):
        dict.__init__(self)

    def get_replacement(self, FromStateIndex, OldDoorId, Default=None):
        change_db = dict.get(self, FromStateIndex)
        if change_db is None: return Default
        result    = change_db.get(OldDoorId)
        if result is None:    return Default
        else:                 return result

    def add(self, IndexOfStateOfConcernedTransistionMap, OldDoorId, NewDoorId):
        assert isinstance(OldDoorId, DoorID)
        assert isinstance(NewDoorId, DoorID)
        change_db = dict.get(self, IndexOfStateOfConcernedTransistionMap)
        if change_db is not None: change_db[OldDoorId] = NewDoorId
        else:                     self[ IndexOfStateOfConcernedTransistionMap] = { OldDoorId: NewDoorId, }

class MegaState_Entry(Entry):
    """________________________________________________________________________
    
    Implements a common base class for Entry classes of MegaState-s. Entries of
    MegaState-s are special in a sense that they implement transitions to more
    than one state. The '.action_db' of an Entry of an AnalyzerState contains
    only transitions (from_index, to_index) where 'to_index == state_index'. A
    MegaState implements two or more AnalyzerState-s, so the 'to_index' may
    have more than one value in keys of '.action_db'.
    
    PRELIMINARY: Documentation of class 'Entry'.

    ___________________________________________________________________________
    """
    def __init__(self):
        Entry.__init__(self)

        # Some transitions into a MegaState_Entry do not require a
        # 'SetStateKey' command. This is true, for example, for the recursive
        # transition in TemplateState-s or the 'on-path-transition' in
        # PathWalkerState-s. 
        #
        # If a transition shared a DoorID with another one which does not
        # contain a 'SetStateKey' command, then this is no longer the case
        # and the transition needs a new DoorID. The relation between the
        # new and the old DoorID is stored in 'self.transition_reassignment_db'.
        
        self.transition_reassignment_candidate_list = []
        self.transition_reassignment_db             = None

    def transition_reassignment_db_construct(self, RelatedMegaStateIndex):
        """Generate new DoorIDs for all TransitionID-s where '.door_id is None'.
           This shall only be the case for originaly recursive transitions, 
           see 'action_db_update()'.
        """
        ## print "#transition_reassignment_db_construct:", RelatedMegaStateIndex
        ## print "#transition_reassignment_candidate_list:", self.transition_reassignment_candidate_list
        ## print "#transition_reassignment_db id:", id(self)
        ## print_callstack()
        assert self.transition_reassignment_db is None

        self.transition_reassignment_db = DoorIdReassignmentDB()

        # All CommandList-s which are subject to DoorID reassignment are set to
        # 'None'. Then 'action_db.categorize()' can determine new DoorID-s.
        old_db = dict((transition_id, self.action_db.get(transition_id).door_id)
                      for dummy, transition_id in self.transition_reassignment_candidate_list)

        for dummy, transition_id in self.transition_reassignment_candidate_list:
            self.action_db.get(transition_id).door_id = None
        
        self.action_db.categorize(RelatedMegaStateIndex)

        for tm_state_index, transition_id in self.transition_reassignment_candidate_list:
            # tm_state_index = index of the state whose transition map is subject to 
            #                  the replacement.
            action = self.action_db.get(transition_id)
            assert action is not None
            self.transition_reassignment_db.add(IndexOfStateOfConcernedTransistionMap = tm_state_index, 
                                                OldDoorId = old_db[transition_id], 
                                                NewDoorId = action.door_id)

        ## print "#transition_reassignment_db:", self.transition_reassignment_db

    def absorb(self, Other):
        assert isinstance(Other, MegaState_Entry)
        assert self.transition_reassignment_db is None
        assert Other.transition_reassignment_db is None

        self.action_db.absorb(Other.action_db)
        self.transition_reassignment_candidate_list.extend(Other.transition_reassignment_candidate_list)


class MegaState(AnalyzerState):
    """________________________________________________________________________
    
    Interface for all derived MegaState-s:

       .implemented_state_index_set():
       
          Set of indices of AnalyzerState-s which have been absorbed by the 
          MegaState.

       .state_index_sequence()

          List of state indices where state_index_sequence[state_key] gives the 
          according state_index.

       .map_state_index_to_state_key(): 
       
          Provides the state_key that the MegaState requires to act on behalf
          of state_index.

       .map_state_key_to_state_index():

          Determines the state_index on whose behalf the MegaState acts, if its
          state_key is as specified.

       '.bad_company'

          Keeps track of indices of AnalyzerState-s which are not good company.
          Algorithms that try to combine multiple MegaState-s into one (e.g.
          'Template Compression') profit from avoiding to combine MegaStates
          where its elements are bad company to each other.

       .finalize_transition_map()

          Adapts the transition_map. When it detects that all elements of a
          'scheme' enter the same state door, it is replaced by the DoorID.  If
          a uniform target state is entered through different doors depending
          on the absorbed state, then it is replaced by a scheme that contains
          the target state multiple times. 

          The transition_map can only be finalized after ALL MegaState-s have
          been generated.
    ___________________________________________________________________________
    """ 
    def __init__(self, TheEntry, TheDropOut, StateIndex):
        # A 'PseudoMegaState' does not implement a 'MegaState_Entry' and 'MegaState_DropOut'.
        # On the long term 'MegaState_DropOut' should be derived from 'DropOut'.
        assert isinstance(TheEntry, Entry), Entry.__class__.__name__
        assert isinstance(TheDropOut, (MegaState_DropOut, DropOut, DropOutIndifferent, DropOutBackwardInputPositionDetection)) 
        assert isinstance(StateIndex, long)

        self.__entry    = TheEntry
        self.__drop_out = TheDropOut
        AnalyzerState.set_index(self, StateIndex)

        # Maintain a list of states with which the state may not combine well
        self.__bad_company = set()
        
        # State Index Sequence: Implemented States (and may be others) in an 
        # ordered Sequence.
        self.__state_index_sequence = None

    @property
    def entry(self):        return self.__entry

    @property
    def drop_out(self):     return self.__drop_out

    @property
    def init_state_f(self): return False

    def state_index_sequence(self):
        assert False, "This function needs to be overwritten by derived class."

    def implemented_state_index_set(self):
        assert False, "This function needs to be overwritten by derived class."

    def map_state_index_to_state_key(self, StateIndex):
        assert False, "This function needs to be overwritten by derived class."

    def map_state_key_to_state_index(self, StateKey):
        assert False, "This function needs to be overwritten by derived class."

    def bad_company_add(self, StateIndex):
        self.__bad_company.add(StateIndex)

    def bad_company_set(self, StateIndexSet):
        self.__bad_company = StateIndexSet

    def bad_company(self):
        """RETURN: List of state indices with which the MegaState does not 
                   combine well.
        """
        return self.__bad_company

    def check_consistency(self, RemainingStateIndexSet):
        # Check the MegaState's consistency
        assert self.entry.action_db.check_consistency()

        # A MegaState shall not change DoorID-s of entry actions,
        # except for transitions inside the MegaState itself.
        for transition_id, action in self.entry.action_db.iteritems():
            if action.door_id.state_index != self.index: continue
            assert transition_id.target_state_index in self.implemented_state_index_set()
            assert transition_id.source_state_index in self.implemented_state_index_set()

        # A state cannot be implemented by two MegaState-s
        # => All implemented states must be from 'RemainingStateIndexSet'
        assert self.implemented_state_index_set().issubset(RemainingStateIndexSet)


class MegaState_DropOut(TypedDict):
    """_________________________________________________________________________
    
    Map: 'DropOut' object --> indices of states that implement the 
                              same drop out actions.

    For example, if four states 1, 4, 7, and 9 have the same drop_out behavior
    DropOut_X, then this is stated by an entry in the dictionary as

             { ...     DropOut_X: [1, 4, 7, 9],      ... }

    For this to work, the drop-out objects must support a proper interaction
    with the 'dict'-objects. Namely, they must support:

             __hash__          --> get the right 'bucket'.
             __eq__ or __cmp__ --> compare elements of 'bucket'.
    ____________________________________________________________________________
    """
    def __init__(self, *StateList):
        """Receives a list of states, extracts the drop outs and associates 
        each DropOut with the state indices that implement it.
        """
        TypedDict.__init__(self, DropOut, set)

        for state in StateList:
            if isinstance(state,  MegaState): 
                self.update(state.drop_out.iteritems())
            else:
                self.absorb(state.index, state.drop_out)
        return

    def get_uniform_prototype(self):
        """Uniform drop-out means, that for all drop-outs mentioned the same
        actions have to be performed. This is the case, if all states are
        categorized under the same drop-out. Thus the dictionary's size
        will be '1'.
        """
        if len(self) != 1: return None
        prototype = self.iterkeys().next()
        return prototype

    def update(self, Iterable):
        for drop_out, state_index_set in Iterable:
            x = self.get(drop_out)
            if x is None: self[drop_out] = copy(state_index_set)
            else:         x.update(state_index_set)

    def add(self, S, D):
        assert False, "Call 'absorb'"

    def absorb(self, StateIndex, TheDropOut):
        x = self.get(TheDropOut)
        if x is None: self[TheDropOut] = set([StateIndex])
        else:         x.add(StateIndex)

class PseudoMegaState(MegaState): 
    """________________________________________________________________________
    
    Represents an AnalyzerState in a way to that it acts homogeneously with
    other MegaState-s. That is, the transition_map is adapted so that it maps
    from a character interval to a MegaState_Transition.

              transition_map:  interval --> MegaState_Transition

    instead of mapping to a target state index.
    ___________________________________________________________________________
    """
    def __init__(self, Represented_AnalyzerState):
        assert not isinstance(Represented_AnalyzerState, MegaState)
        self.__state = Represented_AnalyzerState

        pseudo_mega_state_drop_out = MegaState_DropOut(Represented_AnalyzerState)

        MegaState.__init__(self, self.__state.entry, 
                           pseudo_mega_state_drop_out,
                           Represented_AnalyzerState.index)

        self.__state_index_sequence = [ Represented_AnalyzerState.index ]

        # (*) Transition map that triggers to MegaState_Transition-s 
        #     instead of triggering to DoorID-s.
        # 
        # CAVEAT: In general, it is **NOT TRUE** that if two transitions (x,a) and
        # (x, b) to a state 'x' share a DoorID in the original state, then they
        # share the DoorID in the MegaState. 
        #
        # The critical case is the recursive transition (x,x). It may trigger the
        # same actions as another transition (x,a) in the original state.
        # However, when 'x' is implemented in a MegaState it needs to set a
        # 'state_key' upon entry from 'a'. This is, or may be, necessary to tell
        # the MegaState on which's behalf it has to operate. The recursive
        # transition from 'x' to 'x', though, does not have to set the state_key,
        # since the MegaState still operates on behalf of the same state. While
        # (x,x) and (x,a) have the same DoorID in the original state, their DoorID
        # differs in the MegaState which implements 'x'.
        #
        # THUS: A translation 'old DoorID' --> 'new DoorID' is not sufficient to
        # adapt transition maps!
        #
        # Here, the recursive target is implemented as a 'scheme' in order to
        # prevent that it may be treated as 'uniform' with other targets.
        self.transition_map = TransitionMap.from_iterable(self.__state.transition_map, 
                                                          MegaState_Transition.create)

    def state_index_sequence(self):
        return self.__state_index_sequence

    def implemented_state_index_set(self):
        return set(self.__state_index_sequence)

    def map_state_index_to_state_key(self, StateIndex):
        assert False, "PseudoMegaState-s exist only for analysis. They shall never be implemented."

    def map_state_key_to_state_index(self, StateKey):
        assert False, "PseudoMegaState-s exist only for analysis. They shall never be implemented."

class AbsorbedState_Entry(Entry):
    """________________________________________________________________________

    The information about what transition is implemented by what
    DoorID is stored in this Entry. It is somewhat isolated from the
    AbsorbedState's Entry object.
    ___________________________________________________________________________
    """
    def __init__(self, StateIndex, ActionDB):
        Entry.__init__(self)
        self.__action_db = ActionDB

class AbsorbedState(AnalyzerState):
    """________________________________________________________________________
    
    An AbsorbedState object represents an AnalyzerState which has been
    implemented by a MegaState. Its sole purpose is to pinpoint to the
    MegaState which implements it and to translate the transtions into itself
    to DoorIDs of the implementing MegaState.
    ___________________________________________________________________________
    """
    def __init__(self, AbsorbedAnalyzerState, AbsorbingMegaState):
        AnalyzerState.set_index(self, AbsorbedAnalyzerState.index)
        # The absorbing MegaState may, most likely, contain other transitions
        # than the transitions into the AbsorbedAnalyzerState. Those, others
        # do not do any harm, though. Filtering out those out of the hash map
        # does, most likely, not bring any benefit.
        assert AbsorbedAnalyzerState.index in AbsorbingMegaState.implemented_state_index_set()
        #----------------------------------------------------------------------

        self.__entry     = AbsorbedState_Entry(AbsorbedAnalyzerState.index, 
                                               AbsorbingMegaState.entry.action_db)
        self.absorbed_by = AbsorbingMegaState
        self.__state     = AbsorbedAnalyzerState

    @property
    def drop_out(self):
        return self.__state.drop_out

    @property
    def entry(self): 
        return self.__entry

