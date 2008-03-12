import quex.core_engine.state_machine.index as     state_machine_index
from   quex.core_engine.state_machine.core  import StateMachine, StateInfo
from   quex.core_engine.state_machine.index import map_state_combination_to_index

class StateSet_List:
    def __init__(self, StateMachine):
        self.sm = StateMachine
        #
        # -- map: [state index]  -->  [index of the state set that contains it]
        self.map = {} 
        #
        # -- create: self.state_set_list by initial split of all states.
        self.__initial_split()
        self.size = len(self.state_set_list)

    def get(self, Index):
        return self.state_set_list[Index]

    def __initial_split(self):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

        """   
        self.state_set_list = []

        # (1) Split according to acceptance and non-acceptance
        self.state_set_list.append([])  # state set '0': non-acceptance states
        acceptance_state_set = []       # acceptance states
        for state_index, state in self.sm.states.items():
            if state.is_acceptance(): 
                acceptance_state_set.append(state_index)
            else:                     
                self.state_set_list[0].append(state_index)  # put state into state set 0
                self.map[state_index] = 0                   # note, that it is stored in state set '0'

        # NOTE: Under normal conditions, there **must** be at least one non-acceptance state,
        #       which happens to be the initial state (otherwise nothing would be acceptable).
        #       But, for unit tests etc. we need to live with the possibility that the there 
        #       might be no non-acceptance states.
        if len(self.state_set_list[0]) == 0: del self.state_set_list[0]

        # (2) Split the acceptance states according to their origin. An acceptance
        #     state maching the, for example, an identifier is not equivalent an 
        #     acceptance state thate that matches a number.
        db = {}   
        def db_add(key, state_index):
            if db.has_key(key): db[key].append(state_index)
            else:               db[key] = [ state_index ]                             

        for state_index in acceptance_state_set:
            state = self.sm.states[state_index]
            origin_state_machine_ids = map(lambda origin: origin.state_machine_id, 
                                           state.get_origin_list())
            state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
            db_add(state_combination_id, state_index)

        # (2b) Enter the splitted acceptance state sets.
        i = len(self.state_set_list) - 1           # See 'NOTE' above.
        for state_set in db.values():
            i += 1
            self.state_set_list.append(state_set)  # -- enter the state set.
            for state_index in state_set:          # -- mark for each state in which state
                self.map[state_index] = i          #    set it is stored.



    def split(self, StateSetIndex):
        """RETURNS:  False   if StateSet does not need to be split up any further.
                     True    if the state set requires a split.
        """
        state_set = self.state_set_list[StateSetIndex]
        #
        N         = len(state_set)
        assert N != 0, "State set of size '0'. List = " + repr(state_set_list)
        # only one state in state set => no change possible
        if N == 1: return False    

        # -- choose one arbitrary state (for example state 0) as a prototype
        #    which is compared against the remaining states in the state set.
        prototype_index      = state_set[0]
        prototype            = self.sm.states[prototype_index]
        equivalent_state_set = [ prototype_index ] 

        # -- loop over all remaining states from state set
        i         = 1   # state_set[i] = state index
        element_n = N   # remaining number of elements in state set
        for state_index in state_set[1:]:
            state = self.sm.states[state_index]
            if self.check_equivalence(prototype, state): 
                equivalent_state_set.append(state_index)

        # -- Are all states equivalent?
        if len(equivalent_state_set) == N: return False  # no split! 

        # -- States that are not equivalent (probably most likely) remain in the 
        #    original state set and the ones that are equivalent are put into a new
        #    set at the end of the state set list.
        #    
        #    Delete equivalent states from the original state set
        for state_index in equivalent_state_set:
            i = state_set.index(state_index)
            del state_set[i]

        #    Create the new state set at the end of the list
        self.state_set_list.append(equivalent_state_set)
        # -- Mark in the map the states that have moved to the new state set at the end.
        for state_index in equivalent_state_set:
            self.map[state_index] = self.size
        # -- increase the size counter
        self.size += 1 

        return True

    def check_equivalence(self, This, That):
        """Do state 'This' and state 'That' trigger on the same triggers to the
           same target state?
        """
        transition_list_0 = This.get_transition_list()
        transition_list_1 = This.get_transition_list()

        if len(transition_list_0) != len(transition_list_1): return False

        for t0 in transition_list_0:
            # find transition in 'That' state that contains the same trigger set
            for t1 in transition_list_1:
                if t1.trigger_set == t0.trigger_set: break
            else:
                # no trigger set found in 'That' that corresponds to 'This' => not equivalent
                return False

            target_0 = self.map[t0.target_state_index]
            target_1 = self.map[t1.target_state_index]

            # do both states trigger on the same trigger set to the same target state?
            if target_0 != target_1: return False

        return True
            

def do(SM):
    """Reduces the number of states according to equivalence classes of states. It starts
       with two sets: 
       
            (1) the set of acceptance states, 
                -- these states need to be splitted again according to their origin.
                   acceptance of state machine A is not equal to acceptance of 
                   state machine B.
            (2) the set of non-acceptance states.
       
       Whenever one finds a state in a state set that triggers on the same characters to 
       a different state set, the set has to be split in two sets of states:

           -- the set of states that trigger on trigger 'X' to state set 'K'
           -- the set of states that trigger on trigger 'X' to another state set

       The original state set is replaced by the two new ones. This algorithm is 
       repeated until the state sets do not change anymore.
    """        

    # (*) main algorithm    
    state_set_list = StateSet_List(SM)

    state_set_list_changed_f = True   
    while state_set_list_changed_f:
        # Loop over all sets in state set
        # by default the next state set list is the same
        i                        = 0              # -- loop index of the state set
        state_set_list_changed_f = False
        while i < state_set_list.size - 1:
            i += 1
            if state_set_list.split(i):           
                state_set_list_changed_f = True   # -- a split happend, the state sets changed ...  

    # If all states in the state sets trigger equivalently, then the state set remains
    # nothing has to be done to the new state_set list, because its by default setup that way 
    return create_state_machine(SM, state_set_list)

def create_state_machine(SM, StateSetList):
    # When the list of state sets did not change, it means that no states inside any
    # state set triggers to a different state set on the same trigger. the state sets can
    # become a new state machine. the state set that contains the initial state becomes 
    # the initial state of the new state machine.   
    state_set_containing_initial_state_i = StateSetList.map[SM.init_state_index]
    map_new_state_index = {}
    def create_state_index(StateSetIndex):
        if not map_new_state_index.has_key(StateSetIndex):
            new_index = state_machine_index.get()
            map_new_state_index[StateSetIndex] = new_index
            return new_index
        else:
            return map_new_state_index[StateSetIndex]
                
    result = StateMachine(create_state_index(state_set_containing_initial_state_i),
                          PreConditionStateMachine        = SM.pre_condition_state_machine, 
                          TrivialPreConditionBeginOfLineF = SM.has_trivial_pre_condition_begin_of_line())

    # Build up the state machine out of the remaining state sets
    state_set_idx = -1L
    for state_set in StateSetList.state_set_list:
        ## print "##rss:", state_set
        ## print "##map:", map_new_state_index 
        state_set_idx += 1L
        assert len(state_set) != 0, "State set of size '0'. List = " + repr(StateSetList)

        # States in one set behave all equivalent with respect to target state sets
        # thus only one state from the start set has to be considered.      
        prototype = SM.states[state_set[0]]

        start_index = create_state_index(state_set_idx)
        if not result.states.has_key(start_index):
            result.create_new_state(StateIdx=start_index)

        # If state set contains an acceptance state, then the result is 'acceptance'.
        # (NOTE: The initial split separates acceptance states from those that are not
        #        acceptance states. There can be no state set containing acceptance and 
        #        non-acceptance states) 
        result.set_acceptance(start_index, prototype.is_acceptance())

        for t in prototype.get_transition_list():
            target_index = StateSetList.map[t.target_state_index]
            result.add_transition(start_index, 
                                  t.trigger_set, 
                                  create_state_index(target_index))


        # Merge all core information of the states inside the state set.
        for state_idx in state_set:
            prototype.merge(SM.states[state_idx])

    return result    



