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
with a 'TargetByStateKey'. Given a state_key, the TargetByStateKey provides the
target state index for the given character interval.

The following pinpoints the general idea of a MegaState.

    MegaStateEntry:
 
        ... entry doors of absorbed states ...

    /* Some Specific Actions ... */

    tansition_map( input ) {
        in interval_0:  TargetByStateKey_0[state_key];  --> Target states
        in interval_1:  TargetByStateKey_1[state_key];  --> depending on
        in interval_2:  TargetByStateKey_2[state_key];  --> current input
        ...                                             --> character.
        in interval_N:  TargetByStateKey_N[state_key]; 
    }

    MegaState_DropOut:

        ... drop-out actions of absorbed states ...
_______________________________________________________________________________

This file provides two special classes for to represent 'normal' 
AnalyzerState-s:

-- PseudoTemplateState: represents an AnalyzerState as if it was a 
                    MegaState. This way, it may act homogeneously in 
                    algorithms that work on MegaState-s and AnalyzerState-s
                    at the same time.
 
-- AbsorbedState:   represent an AnalyzerState in the original state database,
                    even though it is absorbed by a MegaState.

_______________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
"""
from quex.engine.analyzer.state.core         import AnalyzerState
from quex.engine.analyzer.mega_state.target  import TargetByStateKey
from quex.engine.analyzer.state.entry        import Entry
from quex.engine.analyzer.state.drop_out     import DropOut, \
                                                    DropOutIndifferent, \
                                                    DropOutBackwardInputPositionDetection
from quex.engine.analyzer.door_id_address_label import DoorID
from quex.engine.analyzer.transition_map     import TransitionMap
from quex.engine.interval_handling           import Interval
from quex.blackboard                         import E_StateIndices

from quex.engine.tools import print_callstack, \
                              TypedDict

from copy import copy

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
        self.__transition_reassignment_db           = None

    @property
    def transition_reassignment_db(self):
        return self.__transition_reassignment_db

    def absorb(self, Other):
        assert isinstance(Other, MegaState_Entry)
        assert self.__transition_reassignment_db is None
        assert Other.__transition_reassignment_db is None
        assert False, "Replaced by 'entry.absorb'"
        self.action_db.absorb(Other.action_db)

        # It is nice to have 'action_db_update' happen in the process of 'finalization'
        # after all absorbtion has taken place. This makes things much less dynamic and
        # much more understandable. Thus, assume that 'action_db_update' has never been
        # called and the 'transition_reassignment_candidate_list' is empty.
        assert len(self.transition_reassignment_candidate_list) == 0
        # self.transition_reassignment_candidate_list.extend(Other.transition_reassignment_candidate_list)

    def action_db_update(self, From, To, FromOutsideCmd, FromInsideCmd):
        """MegaStates may add 'set-state-key-commands' to the CommandLists of
        the state entries. 
        
        For any state which is implemented in a MegaState and which is entered
        from outside a state key MUST be set. For transitions inside a
        MegaState itself, there might be other mechanisms to determine the
        state key.

        'To' and 'From' = indices of a state which is implemented by the
        MegaState.
        
        For any transition if

               .source_state_index == From and .target_state_index == To

        then this transition happens without leaving the MegaState. It happens
        'inside'. For any action associate with a TransitionID

              TransitionID inside => adorn action with 'FromInsideCmd'
              else                => adorn action with 'FromOutsideCmd'

        DoorIDs of transitions which happen from outside MUST remain the same.
        DoorIDs inside the MegaState are subject to reconfiguration. They are
        listed in 'transition_reassignment_candidate_list'.
        """

        for transition_id, action in self.action_db.iteritems():

            if transition_id.target_state_index != To:
                # This transition does not concern the state which is meant.
                continue

            elif transition_id.source_state_index != From:
                cmd = FromOutsideCmd

            else:
                cmd = FromInsideCmd
                # Later we will try to unify all entries from inside.
                self.transition_reassignment_candidate_list.append((From, transition_id))

            if cmd is not None:
                action.command_list.append(cmd)

        return

    def transition_reassignment_db_construct(self, RelatedMegaStateIndex):
        """Generate new DoorIDs for all TransitionID-s where '.door_id is None'.
           This shall only be the case for originaly recursive transitions, 
           see 'action_db_update()'.
        """
        ##print "#transition_reassignment_db_construct:", RelatedMegaStateIndex
        ##print "#transition_reassignment_candidate_list:", self.transition_reassignment_candidate_list
        ## print "#door_id_replacement_db id:", id(self)
        ## print_callstack()
        assert self.__transition_reassignment_db is None


        # All CommandList-s which are subject to DoorID reassignment are set to
        # 'None'. Then 'action_db.categorize()' can determine new DoorID-s.
        for dummy, transition_id in self.transition_reassignment_candidate_list:
            self.action_db.get(transition_id).door_id = None
        
        self.action_db.categorize(RelatedMegaStateIndex)

        self.__transition_reassignment_db = {}
        for tm_state_index, transition_id in self.transition_reassignment_candidate_list:
            # tm_state_index = index of the state whose transition map is subject to 
            #                  the replacement.
            action = self.action_db.get(transition_id)
            assert action is not None
            self.__transition_reassignment_db[transition_id] = action.door_id 

        ##print "#transition_reassignment_db:", self.__transition_reassignment_db
        return

class StateKeyIndexDB(dict):
    """Maintenance of relationships between 'state_keys' of a MegaState and the
       'state_index' of the state which they represent.
                
    The state indices of a MegaState are lined up in some sequence which may
    contain other, non-implemented states (see PathWalkerState).  The
    implemented state index set only contains states which are implemented.

    This may be subtle: A state index may appear in the state index sequence
    while it is not part of the implemented state index.  The happens, for
    example, in the role of a 'terminal' of a path in a PathWalkerState.  Then,
    however, it may appear again as an implemented state, i.e.
    
                        '13' as terminal --.
                                           |
     state_index_sequence: .. [  ][  ][  ][13][  ][  ][  ][13][  ][  ] ..
                                                           |
                               '13' as implemented state --'
    
    Thus, 'state_index_sequence.index(StateIndex)' would not return the 
    correct result. A map is required.
    """
    __slots__ = ("__map_state_index_to_state_key",
                 "__implemented_state_index_set",
                 "__state_index_sequence")

    def __init__(self, StateIndexList, IgnoredListIndex=None):
        self.__map_state_index_to_state_key = {}
        self.__implemented_state_index_set  = set()
        self.__state_index_sequence         = []
        self.extend(StateIndexList, IgnoredListIndex)

    @property
    def state_index_sequence(self): 
        return self.__state_index_sequence

    @property
    def implemented_state_index_set(self): 
        return self.__implemented_state_index_set

    def map_state_key_to_state_index(self, StateKey):   
        result = self.__state_index_sequence[StateKey]
        assert result in self.__implemented_state_index_set
        return result

    def map_state_index_to_state_key(self, StateIndex): 
        assert StateIndex in self.__implemented_state_index_set
        return self.__map_state_index_to_state_key[StateIndex]

    def extend(self, StateIndexList, IgnoredListIndex=None):
        offset = len(self.__state_index_sequence)
        for i, state_index in enumerate(StateIndexList):
            if i == IgnoredListIndex: continue
            self.__map_state_index_to_state_key[state_index] = offset + i

        self.__state_index_sequence.extend(StateIndexList)
        self.__implemented_state_index_set.update(
             x for i, x in enumerate(StateIndexList) if i != IgnoredListIndex
        )

    def not_implemented_yet(self, StateIndexSet):
        """RETURNS: True, if none of the States in StateIndexSet is in
                          .implemented_state_index_set.
                    False, else.
        """
        return self.implemented_state_index_set.isdisjoint(StateIndexSet)

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
    def __init__(self, StateIndex, TheTransitionMap, SkiDb):
        # A 'PseudoTemplateState' does not implement a 'MegaState_Entry' and 'MegaState_DropOut'.
        # On the long term 'MegaState_DropOut' should be derived from 'DropOut'.
        assert isinstance(StateIndex, long)

        self.__entry    = MegaState_Entry()
        self.__drop_out = MegaState_DropOut()
        AnalyzerState.set_index(self, StateIndex)
        # AnalyzerState.__init__(StateIndex, InitStateF, EngineType, TheTransitionMap):

        self.ski_db         = SkiDb
        self.transition_map = TheTransitionMap

        # Maintain a list of states with which the state may not combine well
        self.__bad_company = set()

    @property
    def entry(self): return self.__entry

    @property
    def drop_out(self): return self.__drop_out

    def implemented_state_index_set(self):
        return self.ski_db.implemented_state_index_set

    def state_index_sequence(self):
        return self.ski_db.state_index_sequence

    def map_state_index_to_state_key(self, StateIndex):
        return self.ski_db.map_state_index_to_state_key(StateIndex)

    def map_state_key_to_state_index(self, StateKey):
        return self.ski_db.map_state_key_to_state_index(StateKey)

    def bad_company_add(self, StateIndex):
        self.__bad_company.add(StateIndex)

    def bad_company_set(self, StateIndexSet):
        self.__bad_company = StateIndexSet

    def bad_company(self):
        """RETURN: List of state indices with which the MegaState does not 
                   combine well.
        """
        return self.__bad_company

    def finalize(self, TheAnalyzer, CompressionType):
        # (1.1) Collect all Entry and DropOut objects from implemented states.
        for state_index in self.ski_db.implemented_state_index_set:
            self._finalize_absorb_Entry_DropOut_from_state(TheAnalyzer.state_db[state_index])

        # (1.2) Configure the entry actions, so that the state key is set 
        #       where necessary.
        self._finalize_entry_CommandLists()                    # --> derived class!
        #      => '.transition_reassignment_db'
        self.entry.transition_reassignment_db_construct(self.index)

        # (2) Reconfigure the transition map based on 
        #     '.transition_reassignment_db'
        self._finalize_transition_map()                        # --> derived class!

        # (3) Finalize some specific content
        self._finalize_content(TheAnalyzer)                    # --> derived class!

    def _finalize_absorb_Entry_DropOut_from_state(self, TheState):
        self.entry.action_db.absorb(TheState.entry.action_db)
        self.drop_out.absorb(TheState.index, TheState.drop_out)

    def _finalize_transition_map(self):     
        def get_new_target(TransitionIdToDoorId_db, Target):
            return Target.clone_adapted_self(TransitionIdToDoorId_db)
        self.transition_map.adapt_targets(self.entry.transition_reassignment_db, get_new_target)

    def _finalize_entry_CommandLists(self): 
        assert False, "--> derived class"

    def _finalize_content(self):            
        assert False, "--> derived class"

    def _get_target_by_state_key(self, Begin, End, TargetScheme, StateKey):
        """Given a target in the MegaState-s transition map and the StateKey of the
        represented state, this function returns the resulting DoorID.
        """
        assert False, "--> derived class"

    def verify_transition_map(self, TheAnalyzer):
        """Each state which is implemented by this MegaState has a transition map.
        Given the state key of the represented state the TemplateState must know
        the exact transition map. Exceptions are transitions to DoorID-s which 
        have been replaced.

        This function relies on '._get_target_by_state_key()' being implemented
        by the derived class.
        """
        # Exceptions: replaced DoorID-s. No assumptions made on those targets.
        replaced_door_id_set = set(self.entry.transition_reassignment_db.itervalues())
        self_DoorID_drop_out = DoorID.drop_out(self.index)

        # Iterate over all represented states of the MegaState
        for state_index in self.implemented_state_index_set():
            state_key = self.map_state_index_to_state_key(state_index)

            # TransitionMap of the represented state.
            original_tm = TheAnalyzer.state_db[state_index].transition_map
            # Compare for each interval original target and target(state_key)
            for begin, end, target, target_scheme in TransitionMap.izip(original_tm, self.transition_map):
                target_by_state_key = self._get_target_by_state_key(begin, end, target_scheme, state_key)
                if   target_by_state_key == target:               continue # The target must be the same, or
                elif target_by_state_key in replaced_door_id_set: continue # be a 'replaced one'.
                # A MegaState-s DropOut may represent any DropOut
                elif     target_by_state_key == self_DoorID_drop_out  \
                     and target.drop_out_f():                     continue 

                print "#original:\n"    + original_tm.get_string("hex")
                print "#scheme:\n"      + self.transition_map.get_string("hex")
                print "#selfDropOut:\n" + str(self_DoorID_drop_out)
                print "#StateKey:", state_key
                print "#siseq:", self.ski_db.state_index_sequence
                print "#siseq[StateKey]:", self.ski_db.state_index_sequence[state_key]
                print "# %s: tm -> %s; scheme[%s] -> %s;" % (Interval(begin, end).get_string("hex"), target, state_key, target_by_state_key)
                return False
        return True

    def assert_consistency(self, CompressionType, RemainingStateIndexSet, TheAnalyzer):
        # Check the MegaState's consistency
        assert self.entry.action_db.check_consistency()

        # Check whether the transition map is ok.
        assert self.verify_transition_map(TheAnalyzer)

        # A MegaState shall not change DoorID-s of entry actions,
        # except for transitions inside the MegaState itself.
        for transition_id, action in self.entry.action_db.iteritems():
            if action.door_id.state_index != self.index: continue
            assert transition_id.target_state_index in self.implemented_state_index_set()
            assert transition_id.source_state_index in self.implemented_state_index_set()

        # A state cannot be implemented by two MegaState-s
        # => All implemented states must be from 'RemainingStateIndexSet'
        assert self.implemented_state_index_set().issubset(RemainingStateIndexSet)

        # Check specific consistency (implemented by derived class)
        self._assert_consistency(CompressionType, RemainingStateIndexSet, TheAnalyzer) # --> derived class

    def _assert_consistency(self, CompressionType, RemainingStateIndexSet, TheAnalyzer):            
        assert False, "--> derived class"

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

    def is_uniform(self):
        return len(self) == 1

    def get_uniform_prototype(self):
        """Uniform drop-out means, that for all drop-outs mentioned the same
        actions have to be performed. This is the case, if all states are
        categorized under the same drop-out. Thus the dictionary's size
        will be '1'.

        RETURNS: [0] uniform prototype
                 [1] set of all state indices
        """
        if len(self) != 1: return None, None
        prototype = self.iterkeys().next()

        # Generator of an iteratoer over all state indices
        all_state_indices = set()
        for state_index_list in self.itervalues():
            all_state_indices.update(state_index_list)

        return prototype, all_state_indices

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


