from   quex.engine.analyzer.mega_state.core         import MegaState, \
                                                           MegaState_Transition, \
                                                           MegaState_Entry, \
                                                           MegaState_DropOut
from   quex.engine.analyzer.mega_state.template.candidate  import TargetFactory
from   quex.engine.analyzer.transition_map          import TransitionMap        
from   quex.engine.analyzer.state.entry_action      import SetTemplateStateKey, \
                                                           DoorID, \
                                                           DoorID_Scheme
import quex.engine.state_machine.index              as     index
from   quex.engine.interval_handling                       import Interval

class TemplateState_Entry(MegaState_Entry):
    """________________________________________________________________________

    Entry into a TemplateState. As the base's base class 'Entry' it holds
    information about what CommandList is to be executed upon entry from a
    particular source state.

    PRELIMINARY: Documentation of class 'MegaState_Entry'.

    A TemplateState is a MegaState, meaning it implements multiple states at
    once. Entries into the TemplateState must have an action that sets the
    'state key' for the state that it is about to represent. The 'state key'
    of a PathWalkerState' is the offset of the path iterator from the character
    path's base.

    During analysis, only the '.action_db' is of interest. There the 
    'SetTemplateStateKey' Command is added for each transition. After analysis
    'door_tree_configure()' may be called and those actions are combined
    propperly.
    ___________________________________________________________________________
    """
    def __init__(self, RelatedMegaStateIndex, StateIndexToStateKeyDB, *EntryList):
        MegaState_Entry.__init__(self)

    def action_db_update(self, StateIndex, ActionDb, StateIndexToStateKeyDB):
        """Include 'TheState.entry.action_db' into this state. That means,
        that any mapping:
           
              transition (StateIndex, FromStateIndex) --> CommandList 

        is absorbed in '.action_db'. Additionally, any CommandList must contain
        the 'SetTemplateStateKey' command that sets the state key for the state
        which is currently represented. At each (external) entry into the
        Template state the 'state_key' must be set, so that the template state
        can operate accordingly.

        RETURNS: List of pairs (TransitionID, DoorID) for newly assigned 
                 DoorIDs to old transitions. This should only be recursive
                 transitions.
        """
        ##print "#adb-1: action_db["
        ##for action in TheEntry.action_db.itervalues():
        ##    print "#door_id:", action.door_id
        ##    print "#cmlist:", action.command_list
        for transition_id, action in ActionDb.iteritems():
            clone = action.clone()
            assert clone.door_id is not None
            if transition_id.target_state_index != transition_id.source_state_index: 
                # Add 'SetTemplateStateKey'
                #
                # Determine 'state_key' (an integer value) for state that is
                # entered.  Since TheState may already be a template state, use
                # 'transition_id.state_index' to handle already absorbed states
                # correctly.
                state_key = StateIndexToStateKeyDB[transition_id.target_state_index]
                for command in clone.command_list.misc:
                    if not isinstance(command, SetTemplateStateKey): continue
                    # Adapt the existing 'SetTemplateStateKey' command
                    command.set_value(state_key)
                    break
                else:
                    # Create new 'SetTemplateStateKey' for current state
                    clone.command_list.misc.add(SetTemplateStateKey(state_key))
            else:
                # Recursion => No 'SetTemplateStateKey'
                #
                #   => The state_key does not have to be set (again) at entry.
                #   => It makes sense to have a dedicated DoorID which is going
                #      to be set by 'action_db.categorize()'. The translation
                #      is then documented in '.transition_reassignment_db'.
                self.transition_reassignment_candidate_list.append((StateIndex, transition_id))
                # clone.door_id = None

            # -- The TransitionID contains the state index of the absorbed state.
            # -- No state can be absorbed twice 
            # => It is impossible that 'transition_id' appears as a key before
            assert self.action_db.get(transition_id) == None
            self.action_db.enter(transition_id, clone)

        return

class TemplateState(MegaState):
    """________________________________________________________________________

    A TemplateState implements multiple similar AnalyzerState-s. Its transition
    map, its entry and drop-out sections function based on a 'state_key'. That
    is, when a 'state_key' of an implemented AnalyzerState is set, the
    transition map, the entry and drop-out sections act the same as the
    correspondent sections in the original AnalyzerState.

    ___________________________________________________________________________
    """
    def __init__(self, Candidate):
        StateA = Candidate.state_a
        StateB = Candidate.state_b
        my_index                    = index.get()
        self.__state_a              = StateA
        self.__state_b              = StateB
        self.__state_index_sequence = StateA.state_index_sequence() + StateB.state_index_sequence()
        self.__state_index_to_state_key_db = dict((state_index, i) for i, state_index in enumerate(self.__state_index_sequence))

        # Combined DropOut and Entry schemes are generated by the same function
        entry    = TemplateState_Entry(my_index, self.__state_index_to_state_key_db, StateA.entry, StateB.entry)
        drop_out = MegaState_DropOut(StateA, StateB)
        MegaState.__init__(self, entry, drop_out, my_index)

        for state in [StateA, StateB]:
            self.entry.action_db_update(state.index, state.entry.action_db, 
                                        self.__state_index_to_state_key_db)
        self.entry.transition_reassignment_db_construct(my_index)

        self.__transition_map, \
        self.__target_scheme_n = combine_maps(self.__state_a, self.__state_b, entry.transition_reassignment_db)

        # Compatible with AnalyzerState
        # (A template state can never mimik an init state)
        self.__engine_type = None # StateA.engine_type
        # self.input         = None # StateA.input # get_input_action(StateA.engine_type, InitStateF=False)

        MegaState.bad_company_set(self, self.__state_a.bad_company().union(self.__state_b.bad_company()))

    def _DEBUG_combined_state_indices(self): return self.__state_a.index, self.__state_b.index

    @property 
    def transition_map(self): 
        return self.__transition_map

    @property
    def target_scheme_n(self):  
        return self.__target_scheme_n

    def state_index_sequence(self):    
        return self.__state_index_sequence

    def map_state_index_to_state_key(self, StateIndex):
        return self.__state_index_to_state_key_db[StateIndex]

    def map_state_key_to_state_index(self, StateKey):
        return self.__state_index_sequence[StateKey]

    def implemented_state_index_list(self):    
        return self.__state_index_sequence

def combine_maps(StateA, StateB, ReassignedTransitionDB):
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
       In a TemplateState, the intervals are associated with MegaState_Transition 
       objects. A MegaState_Transition object tells the target state dependent
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

        (1)    self.state_index_sequence[state_key] == state_index

    where 'state_index' is the number by which the state is identified inside
    its state machine. Correspondingly, for a given TemplateMegaState_Target T 

        (2)                   T[state_key]

    gives the target of the template if it operates for 'state_index' determined
    from 'state_key' by relation (1). The state index list approach facilitates the
    computation of target schemes. For this reason no dictionary
    {state_index->target} is used.

    NOTE: To this point, there is no '.relate_to_door_ids()' required in the
          transition map. A transition map such as 

              [INTERVAL]   [TARGET]
              [-oo, 97]    --> DropOut
              [98]         --> Scheme((12, 32, DROP_OUT))
              [99]         --> Scheme((DROP_OUT, 13, 51))
              [100, oo]    --> DropOut

          lets find the transition '(source_state_index, to_state_index)' for each
          entry in a scheme. E.g. the second entry in the second scheme is the
          target state '32'. The 'state_index_sequence' might tell that the second
          entry in a scheme is to represent the transitions of state '57'. Then,
          it is clear that the door relating to transition '57->32' must be targetted.
    """
    if ReassignedTransitionDB is None:
        reassignment_db_a = None
        reassignment_db_b = None
    else:
        reassignment_db_a = ReassignedTransitionDB.get(StateA.index)
        reassignment_db_b = ReassignedTransitionDB.get(StateB.index)

    ##print "#reassignment_db_a:", StateA.index, reassignment_db_a
    ##print "#reassignment_db_b:", StateB.index, reassignment_db_b

    def real_target(ReassignmentDB, Target):
        if ReassignmentDB is None: return Target
        if   isinstance(Target, DoorID):           
            replacement = ReassignmentDB.get(Target)
            if replacement is None: return Target
            else:                   return MegaState_Transition.create(replacement)

        elif isinstance(Target, MegaState_Transition): 
            replacement = Target.replace_self(ReassignmentDB)
            if replacement is None: return Target
            else:                   return replacement

        else:                                      
            assert False

    def target(a_target, b_target):
        a_target = real_target(reassignment_db_a, a_target)
        b_target = real_target(reassignment_db_b, b_target)
        return factory.get(a_target, b_target)

    StateA.transition_map.assert_adjacency(TotalRangeF=True)
    StateB.transition_map.assert_adjacency(TotalRangeF=True)

    MegaState_Transition.init() # Initialize the tracking of generated MegaState_Transition-s
    factory = TargetFactory(StateA, StateB)

    result = TransitionMap.from_iterable(
        ((Interval(begin, end), target(a_target, b_target)))
        for begin, end, a_target, b_target in TransitionMap.izip(StateA.transition_map, 
                                                                 StateB.transition_map)
    )

    # Return the database of generated MegaState_Transition objects
    mega_state_target_db = MegaState_Transition.disconnect_object_db()
    # Number of different target schemes:
    scheme_n = 0
    for x in (key for key in mega_state_target_db.iterkeys() if isinstance(key, DoorID_Scheme)):
        scheme_n += 1

    return result, scheme_n

