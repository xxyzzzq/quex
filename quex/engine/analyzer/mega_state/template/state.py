from   quex.engine.analyzer.mega_state.core         import MegaState, \
                                                           StateKeyIndexDB
from   quex.engine.analyzer.mega_state.target       import TargetByStateKey
from   quex.engine.analyzer.transition_map          import TransitionMap        
from   quex.engine.analyzer.state.core              import Processor
from   quex.engine.commands.core           import TemplateStateKeySet
import quex.engine.state_machine.index              as     index
from   quex.engine.interval_handling                import Interval
from   quex.engine.tools                            import typed, \
                                                           UniformObject

class TemplateState(MegaState):
    """_________________________________________________________________________

     Implements multiple AnalyzerState-s in one single state. Its transition
     map, its entry and drop-out sections function are based on a 'state_key'. 
     That is, when a 'state_key' of an implemented AnalyzerState is set, the
     transition map, the entry and drop-out sections act the same as the
     correspondent sections in the original AnalyzerState.
    ____________________________________________________________________________
    """
    def __init__(self, Candidate):
        StateA = Candidate.state_a
        StateB = Candidate.state_b

        # Combined DropOut and Entry schemes are generated by the same function
        transition_map, target_scheme_n = combine_maps(StateA.transition_map, StateB.transition_map)

        ski_db = StateKeyIndexDB(StateA.state_index_sequence() + StateB.state_index_sequence())
        MegaState.__init__(self, index.get(), transition_map, ski_db)

        self.uniform_entry_CommandList = UniformObject.from_iterable((
                                                       StateA.uniform_entry_CommandList,
                                                       StateB.uniform_entry_CommandList))

        self.__target_scheme_n = target_scheme_n
        self.__engine_type     = None # StateA.engine_type

        MegaState.bad_company_set(self, StateA.bad_company().union(StateB.bad_company()))

    def _finalize_entry_CommandLists(self):
        """If a state is entered from outside, then the 'state_key',
        needs to be set. When a represented state iterates on itself, then the
        state_key does not change and it has not to be set.

        NOTE: Here, it must be ensured that the DoorID-s for entries from 
              outside remain the same! This way, any external transition map
              may remain the same.
        """
        # Recursive entries: The represented state remains the same. No state key
        #                    needs to be set.
        # From outside, and any non-recursive entry: A new state key needs to be
        #                    assigned.
        for state_index in self.ski_db.implemented_state_index_set:
            state_key = self.ski_db.map_state_index_to_state_key(state_index)
            # Update sets inside transition's 'door_id = None' and adds
            # the transition to 'transition_reassignment_candidate_list'.
            self.entry.action_db_update(From           = state_index,
                                        To             = state_index, 
                                        FromOutsideCmd = TemplateStateKeySet(state_key),
                                        FromInsideCmd  = None)
        return

    def _finalize_content(self, TheAnalyzer):
        """Nothing to be done."""
        pass

    @property
    def target_scheme_n(self):  
        return self.__target_scheme_n

    def _get_target_by_state_key(self, Begin, End, TargetScheme, StateKey):
        """A TemplateState may find the target by using the StateKey as an index
        into an array 'TargetScheme[State]'. For DoorID-s which have been replaced
        this does not need to work.

        NOTE: This function does not need to work for DoorID-s which are mentioned
              in 'self.entry.transition_reassignment_db'.
        """
        return TargetScheme.get_door_id_by_state_key(StateKey)

    def _assert_consistency(self, CompressionType, RemainingStateIndexSet, TheAnalyzer):            
        pass

class PseudoTemplateState(MegaState): 
    """________________________________________________________________________
    
    Represents an AnalyzerState in a way to that it acts homogeneously with
    other MegaState-s. That is, the transition_map is adapted so that it maps
    from a character interval to a TargetByStateKey.

              transition_map:  interval --> TargetByStateKey

    instead of mapping to a target state index.
    ___________________________________________________________________________
    """
    @typed(DropOutCatcher=Processor)
    def __init__(self, Represented_AnalyzerState, DropOutCatcher):
        assert not isinstance(Represented_AnalyzerState, MegaState)
        state_index            = Represented_AnalyzerState.index
        transition_map         = Represented_AnalyzerState.transition_map

        adapted_transition_map = transition_map.relate_to_TargetByStateKeys(state_index, 
                                                                            DropOutCatcher)
        ski_db                 = StateKeyIndexDB([state_index])
        MegaState.__init__(self, state_index, adapted_transition_map, ski_db)

        # Uniform Entry: In contrast to path compression, here we consider 
        #                all entries into the MegaState. 
        self.uniform_entry_CommandList = UniformObject()
        for action in Represented_AnalyzerState.entry.itervalues():
            self.uniform_entry_CommandList <<= action.command_list
            if self.uniform_entry_CommandList.is_uniform() == False:
                break # No more need to investigate

        self.entry.absorb(Represented_AnalyzerState.entry)

    @property
    def target_scheme_n(self):  
        return 0

    def _finalize_transition_map(self, TheAnalyzer):
        pass # Nothing to be done

    def _finalize_entry_CommandLists(self): 
        pass

    def _finalize_content(self):            
        pass

def combine_maps(TransitionMap_A, TransitionMap_B):
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
       In a TemplateState, the intervals are associated with TargetByStateKey 
       objects. A TargetByStateKey object tells the target state dependent
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
       Thus, TargetByStateKey objects must be combined with trigger targets
       and other TargetByStateKey objects.

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
    keys are used as indices into TargetByStateKey-s. The 'state_key' of a given
    state relates to the 'state_index' by

        (1)    self.state_index_sequence[state_key] == state_index

    where 'state_index' is the number by which the state is identified inside
    its state machine. Correspondingly, for a given TargetByStateKey T 

        (2)                   T[state_key]

    gives the target of the template if it operates for 'state_index' determined
    from 'state_key' by relation (1). The state index list approach facilitates the
    computation of target schemes. For this reason no dictionary
    {state_index->target} is used.

    NOTE: To this point, there is no '.relate_to_DoorIDs()' required in the
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
    TransitionMap_A.assert_adjacency(TotalRangeF=True)
    TransitionMap_B.assert_adjacency(TotalRangeF=True)

    scheme_pair_db = {}
    result = TransitionMap.from_iterable(
        ((Interval(begin, end), 
         TargetByStateKey.from_2_TargetByStateKeys(a_target, b_target, scheme_pair_db)))
        for begin, end, a_target, b_target in TransitionMap.izip(TransitionMap_A, TransitionMap_B)
    )

    # Number of different target schemes:
    scheme_n = len(scheme_pair_db)
    return result, scheme_n

