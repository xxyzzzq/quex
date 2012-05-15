from   quex.engine.generator.state.transition.core  import assert_adjacency
from   quex.engine.analyzer.state.core              import get_input_action
from   quex.engine.analyzer.state.entry             import Entry
from   quex.engine.analyzer.state.entry_action      import SetTemplateStateKey, DoorID
from   quex.engine.analyzer.mega_state.core         import MegaState, \
                                                           MegaState_Target, \
                                                           MegaState_Target_DROP_OUT, \
                                                           MegaState_DropOut, \
                                                           get_state_list
from   quex.engine.interval_handling                import Interval
from   quex.blackboard                              import E_StateIndices

from   itertools   import chain
from   collections import defaultdict
import sys

class TemplateState_Entry(Entry):
    """MegaState-Entry for Template States.

       Recall some things about a state's 'Entry': 
       
       -- An 'Entry' holds information about what actions are to be performed
          upon entry into a state from a specific 'source state'. 

       -- A 'TransitionID' consists of a pair 'source state index' and 'target
          state index' and identifies a state transition.

       -- A 'CommandList' contains a list commands to be coded.
                  
       -- The 'Entry.action_db' maps TransitionID-s to CommandList objects.
          That is, it tells what commands have to be executed when the state is
          entered from a specific source state.

       -- There are common elements in command lists. To avoid double code,
          these are analyzed and the result is the 'door tree'.  Each 'source
          state' can be associated with a door in the door tree.

       -- 'Entry.door_db' maps:       'TransitionID' --> 'DoorID'
       -- 'Entry.transition_db' maps: 'DoorID' --> 'TransitionID'
    """
    def __init__(self, StateIndex, StateIndexToStateKeyDB, *EntryList):
        Entry.__init__(self, StateIndex, [])
        for entry in EntryList:
            self.update(entry, StateIndexToStateKeyDB)

        Entry.door_tree_configure(self, StateIndex)

    def update(self, TheEntry, StateIndexToStateKeyDB):
        """Include 'TheState.entry.action_db' into this state. That means,
           that any mapping:
           
                transition (StateIndex, FromStateIndex) --> CommandList 

           is absorbed in 'self.__action_db'. Additionally, any command list
           must contain the 'SetTemplateStateKey' command that sets the state
           key for TheState. At each (external) entry into the Template state
           the 'state_key' must be set, so that the template state can operate
           accordingly.  
        """
        for transition_id, action in TheEntry.action_db.iteritems():
            clone = action.clone()
            if transition_id.state_index == transition_id.from_state_index: 
                # Recursion of a state will be a recursion of the template state.
                #   => The state_key does not have to be set (again) at entry.
                #   => With the "door_tree_configure()" comes an elegant consequence:
                # 
                # ALL RECURSIVE TARGETS INSIDE THE TEMPLATE WILL ENTER THROUGH THE
                # SAME DOOR, AS LONG AS THEY DO THE SAME THING. 
                # 
                # RECURSION WILL BE A SPECIAL CASE OF 'SAME DOOR' TARGET WHICH HAS 
                # NOT TO BE DEALT WITH SEPARATELY.
                pass
            else:
                # Not recursive => add control command 'SetTemplateStateKey'
                #
                # Determine 'state_key' (an integer value) for state that is
                # entered.  Since TheState may already be a template state, use
                # 'transition_id.state_index' to handle already absorbed states
                # correctly.
                state_key = StateIndexToStateKeyDB[transition_id.state_index]
                for command in clone.command_list.misc:
                    if not isinstance(command, SetTemplateStateKey): continue
                    # Adapt the existing 'SetTemplateStateKey' command
                    command.set_value(state_key)
                    break
                else:
                    # Create new 'SetTemplateStateKey' for current state
                    clone.command_list.misc.add(SetTemplateStateKey(state_key))

            self.action_db[transition_id] = clone

class TemplateState(MegaState):
    """A TemplateState is a state that is implemented to represent multiple
       similar states. For this it keeps a special transition map. If the
       target state for a character interval depends on the represented state,
       there is a target map which together with a 'state key' delivers the
       target state when the templates acts on behalf of the state key's state.

       The template states are combined successively by the combination of 
       two states where each one of them may also be a TemplateState. The
       combination happens by means of the functions:
       
          self.__update_entry(...)  Which takes over the mappings from 
                                    transition_id to command list. Also, 
                                    it adds the 'SetTemplateStateKey' for each
                                    entry.

          combine_maps(...) which combines the transition maps of the 
                            two states into a single transition map that
                            may contain MegaState_Target-s. 
                               
          combine_drop_out_scheme(...) which combines DropOut and Entry schemes
                                       of the two states.

       Notably, the derived class TemplateStateCandidate takes an important
       role in the construction of the TemplateState.
    """
    def __init__(self, StateA, StateB, TheAnalyzer):
        # The 'index' remains None, as long as the TemplateState is not an 
        # accepted element of a state machine. This makes sense, in particular
        # for TemplateStateCandidates (derived from TemplateState). 
        MegaState.__init__(self, TheAnalyzer)

        self.__analyzer             = TheAnalyzer
        self.__state_index_list     = get_state_list(StateA) + get_state_list(StateB)
        state_index_to_state_key_db = dict((state_index, i) for i, state_index in enumerate(self.__state_index_list))

        # Combined DropOut and Entry schemes are generated by the same function
        self.__entry    = TemplateState_Entry(self.index, state_index_to_state_key_db, StateA.entry, StateB.entry)
        self.__drop_out = MegaState_DropOut(StateA, StateB)

        # Adapt the door ids of the transition maps and bring them all into a form of 
        # (interval --> MegaState_Target)
        tm_a = self.__get_adapted_transition_map(StateA)
        tm_b = self.__get_adapted_transition_map(StateB)

        self.transition_map,    \
        self.__target_scheme_list = combine_maps(StateA, tm_a, StateB, tm_b)

        # Compatible with AnalyzerState
        # (A template state can never mimik an init state)
        self.__engine_type = StateA.engine_type
        self.input         = get_input_action(StateA.engine_type, InitStateF=False)

    @property
    def target_scheme_list(self):  return self.__target_scheme_list
    @property
    def entry(self):               return self.__entry
    @property
    def drop_out(self):            return self.__drop_out
    @property
    def state_index_list(self):    return self.__state_index_list

    def map_state_index_to_state_key(self, StateIndex):
        return self.__state_index_list.index(StateIndex)

    def implemented_state_index_list(self):    
        return self.__state_index_list

    def __get_local_door_id(self, StateIndex, FromStateIndex):
        """If the target state is implemented in this template, then return 
           a locally implemented door. Otherwise, we return a 'standard door'
           of the original states. Later they may be replaced with the 
           doors of their mega states, if they are implemented elsewhere.
        """
        door_id = self.entry.get_door_id(StateIndex, FromStateIndex)
        if door_id is not None:
            # We implement the 'StateIndex' so return a local door from the template
            return door_id
        # Return the 'standard door' of state 'StateIndex' from outside the template
        return self.__analyzer.state_db[StateIndex].entry.get_door_id(StateIndex, FromStateIndex)

    def __get_adapted_transition_map(self, State):
        def adapt(Target):
            """Transitions to states are transformed into transitions to MegaState_Targets.
               That is intervals are associated with 'doors' instead of target states.
            """
            if Target == E_StateIndices.DROP_OUT: 
                return MegaState_Target_DROP_OUT
            else:
                assert isinstance(Target, (int, long))
                # If 'Target' is a recursive target of the other state, then there 
                # is no problem. We know the exact transition (StateIndex, FromStateIndex)
                # and 'self.entry.get_door_id()' delivers the correct result. This
                # is not so for MegaState_Target-s (see adapt_MegaState_Target())
                return MegaState_Target.create(self.__get_local_door_id(Target, State.index))

        def adapt_MegaState_Target(Target):
            """A transition_map can refer to local door ids, as they are implemented
               by this template, or door_ids of 'normal original states'.
               Thus, transitions of an existing template, must de-translated door ids
               that relate to itself, and associate transitions to states which are
               implemented here with local door ids.
            """
            def __adapt(door_id):
                if door_id == E_StateIndices.DROP_OUT:
                    # Nothing to be done
                    return 
                elif door_id.state_index == State.index:
                    transition_id = State.entry.transition_db[door_id][0]
                elif door_id.state_index == self.index:
                    # It may very well be that the MegaState_Target object is referred multiple
                    # times in the same transition map. Thus, it may have been adapted before.
                    # This case is detected by 'door_id.state_index == self.index', which 
                    # means that nothing is to be done.
                    return 
                else:
                    original_state = self.__analyzer.state_db.get(door_id.state_index)
                    if door_id.state_index in self.implemented_state_index_list():
                        for transition_id in original_state.entry.transition_db[door_id]:
                            if transition_id.state_index != transition_id.from_state_index: 
                                break
                        else:
                            assert False, "There MUST be a non-recursive transition to '%s'." % door_id.state_index
                    else:
                        if original_state is None:
                            # The door belongs to a meta state. Meta states are not implemented
                            # by other meta states. Thus, the door is fine as it is.
                            return
                        transition_id = original_state.entry.transition_db[door_id][0]

                return self.__get_local_door_id(transition_id.state_index, 
                                                transition_id.from_state_index)

            if Target.drop_out_f:    
                return Target

            # The '__adapt' function may require an adaption of a door_id. If
            # so, the target needs to be cloned, so that the change does not
            # effect the original target.
            result = Target
            if result.door_id is not None:  
                new_door_id = __adapt(result.door_id)
                if new_door_id is not None: 
                    result = result.clone() # disconnect from original
                    result.door_id.state_index = new_door_id.state_index
                    result.door_id.door_index  = new_door_id.door_index 
                    
            else:
                cloned_f = False
                for i, door_id in enumerate(result.scheme):
                    new_door_id = __adapt(door_id)
                    if new_door_id is None: continue
                    if not cloned_f: 
                        result   = result.clone() # disconnect from original
                        cloned_f = True
                    result.scheme[i].state_index = new_door_id.state_index
                    result.scheme[i].door_index  = new_door_id.door_index 

            return result

        if isinstance(State, TemplateState):
            return [(interval, adapt_MegaState_Target(target)) for interval, target in State.transition_map ]
        else:
            return [(interval, adapt(target))                  for interval, target in State.transition_map ]

def combine_maps(StateA, AdaptedTM_A, StateB, AdaptedTM_B):
    """RETURNS:

          -- Transition map = combined transition map of StateA and StateB.

          -- List of target schemes that have been identified.

       NOTE: 

       If the entries of both states are uniform, then a transition to itself
       of both states can be implemented as a recursion of the template state
       without knowing the particular states.

       EXPLANATION:
    
       This function combines two transition maps. A transition map is a list
       of tuples:

            [
              ...
              (interval, target)
              ...
            ]

       Each tuple tells about a character range [interval.begin, interval.end)
       where the state triggers to the given target. In a normal AnalyzerState
       the target is the index of the target state. In a TemplateState, though,
       multiple states are combined. A TemplateState operates on behalf of a
       state which is identified by its 'state_key'. 
       
       If two states (even TemplateStates) are combined the trigger maps
       are observed, e.g.

            Trigger Map A                    Trigger Map B
                                                                          
            [                                [
              ([0,  10),   DropOut)            ([0,  10),   State_4)
              ([10, 15),   State_0)            ([10, 15),   State_1)
              ([15, 20),   DropOut)            ([15, 20),   State_0)
              ([20, 21),   State_1)            ([20, 21),   DropOut)
              ([21, 255),  DropOut)            ([21, 255),  State_0)
            ]                                ]                           


       For some intervals, the target is the same. But for some it is different.
       In a TemplateState, the intervals are associated with MegaState_Target 
       objects. A MegaState_Target object tells the target state dependent
       on the 'state_key'. The above example may result in a transition map
       as below:

            Trigger Map A                   
                                                                          
            [     # intervals:   target schemes:                           
                  ( [0,  10),    { A: DropOut,   B: State_4, },
                  ( [10, 15),    { A: State_0,   B: State_1, },
                  ( [15, 20),    { A: DropOut,   B: State_0, },
                  ( [20, 21),    { A: State_1,   B: DropOut, },
                  ( [21, 255),   { A: DropOut,   B: State_0, },
            ]                                                           

       Note, that the 'scheme' for interval [12, 20) and [21, 255) are identical.
       We try to profit from it by storing only it only once. A template scheme
       is associated with an 'index' for reference.

       TemplateStates may be combined with AnalyzerStates and other TemplateStates.
       Thus, MegaState_Targets must be combined with trigger targets
       and other MegaState_Targets.

       NOTE:

       The resulting target map results from the combination of both transition
       maps, which may introduce new borders, e.g.
    
                     |----------------|           (where A triggers to X)
                          |---------------|       (where B triggers to Y)

       becomes
                     |----|-----------|---|
                        1       2       3

       where:  Domain:     A triggers to:     B triggers to:
                 1              X               Nothing
                 2              X                  Y
                 3           Nothing               Y

    -----------------------------------------------------------------------------
    Transition maps of TemplateState-s function based on 'state_keys'. Those state
    keys are used as indices into TemplateMegaState_Targets. The 'state_key' of a given
    state relates to the 'state_index' by

        (1)    self.state_index_list[state_key] == state_index

    where 'state_index' is the number by which the state is identified inside
    its state machine. Correspondingly, for a given TemplateMegaState_Target T 

        (2)                   T[state_key]

    gives the target of the template if it operates for 'state_index' determined
    from 'state_key' by relation (1). The state index list approach facilitates the
    computation of target schemes. For this reason no dictionary
    {state_index->target} is used.
    """
    def __help(TM):
        assert_adjacency(TM, TotalRangeF=True)
        return TM, len(TM)

    TransitionMapA, LenA = __help(AdaptedTM_A)
    TransitionMapB, LenB = __help(AdaptedTM_B)


    # Intervals in trigger map are always adjacent, so the '.begin' member is
    # not required.
    scheme_db = TargetSchemeDB(StateA, StateB)
    result    = []
    prev_end  = - sys.maxint
    i                = 0 # iterator over TransitionMapA
    k                = 0 # iterator over TransitionMapB
    i_itvl, i_target = TransitionMapA[i]
    k_itvl, k_target = TransitionMapB[k]
    while not (i == LenA - 1 and k == LenB - 1):
        end    = min(i_itvl.end, k_itvl.end)

        target = scheme_db.get_target(i_target, k_target)
        assert isinstance(target, MegaState_Target)

        result.append((Interval(prev_end, end), target))
        prev_end  = end

        if   i_itvl.end == k_itvl.end: 
            i += 1; i_itvl, i_target = TransitionMapA[i]
            k += 1; k_itvl, k_target = TransitionMapB[k]
        elif i_itvl.end <  k_itvl.end: 
            i += 1; i_itvl, i_target = TransitionMapA[i]
        else:                          
            k += 1; k_itvl, k_target = TransitionMapB[k]

    # Treat the last trigger interval
    target = scheme_db.get_target(TransitionMapA[-1][1], TransitionMapB[-1][1])

    result.append((Interval(prev_end, sys.maxint), target))

    return result, scheme_db.get_scheme_list()

class TargetSchemeDB(dict):
    """A TargetSchemeDB keeps track of existing target state combinations.
       If a scheme appears more than once, it does not get a new index. By means
       of the index it is possible to avoid multiple definitions of the same 
       scheme, later.
    """
    def __init__(self, StateA, StateB):
        dict.__init__(self)
        self.__state_a_state_index_list_length = len(get_state_list(StateA))
        self.__state_a_index                   = StateA.index
        self.__state_b_state_index_list_length = len(get_state_list(StateB))
        self.__state_b_index                   = StateB.index
        self.setup_function_pointers(StateA, StateB)

    def get_target(self, TA, TB):
        assert isinstance(TA, MegaState_Target) 
        assert isinstance(TB, MegaState_Target) 

        if self.A_drop_out(TA):
            if self.B_drop_out(TB):
                return MegaState_Target_DROP_OUT
            TA_scheme = (E_StateIndices.DROP_OUT,) * self.__state_a_state_index_list_length

        elif self.A_is_scheme(TA):
            TA_scheme = TA.scheme

        else:
            if (not self.B_is_scheme(TB)) and self.A_B_are_same_door_id(TA, TB):
                return self.A_or_B_get_MegaState_Target_from_door_id(TA, TB)
            TA_scheme = self.A_get_scheme(TA, self.__state_a_index, self.__state_a_state_index_list_length)

        if self.B_drop_out(TB):
            # TA was not drop-out, otherwise we would have returned earlier
            TB_scheme = (E_StateIndices.DROP_OUT,) * self.__state_b_state_index_list_length

        elif self.B_is_scheme(TB):
            TB_scheme = TB.scheme

        else:
            # TA was not the same door, otherwise we would have returned earlier
            TB_scheme = self.B_get_scheme(TB, self.__state_b_index, self.__state_b_state_index_list_length)

        return self.get_MegaState_Target_from_scheme(TA_scheme, TB_scheme)

    def get_MegaState_Target_from_scheme(self, SchemeA, SchemeB):
        """Checks whether the combination is already present. If so, the reference
           to the existing target scheme is returned. If not a new scheme is created
           and entered into the database.

           The Targets must be a tuple, such as 

              (1, E_StateIndices.DROP_OUT, 4, ...)

           which tells that if the template operates with

              -- state_key = 0 (first element) there must be a transition to state 1, 
              -- state_key = 1 (second element), then there must be a drop-out,
              -- state_key = 2 (third element), then transit to state 4,
              -- ...
        """
        assert isinstance(SchemeA, tuple)
        assert isinstance(SchemeB, tuple)

        scheme = SchemeA + SchemeB

        for target in scheme:
            assert isinstance(target, DoorID) or target == E_StateIndices.DROP_OUT 

        result = dict.get(self, scheme)
        if result is None: 
            new_index    = len(self)
            result       = MegaState_Target.create(scheme, new_index)
            self[scheme] = result

        return result

    def get_scheme_list(self):
        result = self.values()
        for element in result:
            assert element.scheme is not None
        return self.values()

    def setup_function_pointers(self, StateA, StateB):
        a_ms_f = True# isinstance(StateA, MegaState_Target)
        b_ms_f = True# isinstance(StateB, MegaState_Target)
        if a_ms_f:
            self.A_drop_out   = self.MS_drop_out
            self.A_is_scheme  = self.MS_is_scheme
            self.A_get_scheme = self.MS_get_scheme
        else:
            self.A_drop_out   = self.S_drop_out
            self.A_is_scheme  = self.S_is_scheme
            self.A_get_scheme = self.S_get_scheme

        if b_ms_f:
            self.B_drop_out   = self.MS_drop_out
            self.B_is_scheme  = self.MS_is_scheme
            self.B_get_scheme = self.MS_get_scheme
        else:
            self.B_drop_out   = self.S_drop_out
            self.B_is_scheme  = self.S_is_scheme
            self.B_get_scheme = self.S_get_scheme

        if a_ms_f:
            if b_ms_f:
                self.A_B_are_same_door_id                     = self.MS_MS_are_same_door_id
                self.A_or_B_get_MegaState_Target_from_door_id = self.MS_MS_get_MegaState_Target_from_door_id
            else:
                self.A_B_are_same_door_id                     = self.MS_S_are_same_door_id
                self.A_or_B_get_MegaState_Target_from_door_id = self.MS_S_get_MegaState_Target_from_door_id
        else:
            if b_ms_f:
                self.A_B_are_same_door_id                     = self.S_MS_are_same_door_id
                self.A_or_B_get_MegaState_Target_from_door_id = self.S_MS_get_MegaState_Target_from_door_id
            else:
                self.A_B_are_same_door_id                     = self.S_S_are_same_door_id
                self.A_or_B_get_MegaState_Target_from_door_id = self.S_S_get_MegaState_Target_from_door_id

    def MS_drop_out(self, T):   return T.drop_out_f
    def S_drop_out(self, T):    return T == E_StateIndices.DROP_OUT
    def MS_is_scheme(self, T):  return T.door_id is None
    def S_is_scheme(self, T):   return False
    # Assume, T is proven to be a 'door_id'
    def MS_get_scheme(self, T, StateIndex, StateN): return (T.door_id,) * StateN
    def S_get_scheme(self, T, StateIndex, StateN):  return (self.get_door_id(StateIndex, T),) * StateN

    # Assume, TA and TB is proven to be a 'door_id'
    def MS_MS_are_same_door_id(self, TA, TB): return TA.door_id == TB.door_id
    def MS_S_are_same_door_id(self, TA, TB):  return TA.door_id == self.get_door_id(self.__state_b_index, TB)
    def S_MS_are_same_door_id(self, TA, TB):  return self.get_door_id(self.__state_a_index, TA) == TB.door_id
    def S_S_are_same_door_id(self, TA, TB): 
        return self.get_door_id(self.__state_a_index, TA) == self.get_door_id(self.__state_b_index, TB)

    # Assume, TA and TB is proven to be have same 'door_id'; return one of them 
    def MS_MS_get_MegaState_Target_from_door_id(self, TA, TB): return TA
    def MS_S_get_MegaState_Target_from_door_id(self, TA, TB):  return TA
    def S_MS_get_MegaState_Target_from_door_id(self, TA, TB):  return TB
    def S_S_get_MegaState_Target_from_door_id(self, TA, TB):
        return MegaState_Target.create(self.get_door_id(self.__state_a_index, TA))


