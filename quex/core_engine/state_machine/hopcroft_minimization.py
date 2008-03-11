import quex.core_engine.state_machine.index as     state_machine_index
from   quex.core_engine.state_machine.core  import StateMachine, StateInfo
from   quex.core_engine.state_machine.index import map_state_combination_to_index

class StateSet_List:
    def __init__(self, StateMachine):
        self.sm             = StateMachine
        self.state_set_list = self.__initial_split()
        self.size           = len(self.state_set_list)

        ## print "##", self.sm.get_string()
        ## print "##", self.state_set_list

    def get(self, Index):
        return self.state_set_list[Index]

    def __initial_split(self):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

        """   
        acceptance_state_list     = []
        non_acceptance_state_list = []
        for state_idx, state in self.sm.states.items():
            if state.is_acceptance(): acceptance_state_list.append(state_idx)
            else:                     non_acceptance_state_list.append(state_idx)

        # map: set of original states ---> state indices that are of this origin
        db = {}   
        def db_add(key, list_element):
            if db.has_key(key): db[key].append(list_element)
            else:               db[key] = [ list_element ]                             

        for state_index in acceptance_state_list:
            origin_state_machine_ids = map(lambda origin: 
                                           origin.state_machine_id, 
                                           self.sm.states[state_index].get_origin_list())
            state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
            db_add(state_combination_id, state_index)

        # each 'value' (belonging to a key) represents the set of states that have the
        # same combination of original states
        result = db.values()
            
        if non_acceptance_state_list != []: 
            return result + [ non_acceptance_state_list ]
                
        return result

    def split(self, StateSet):
        """RETURNS:  False   if StateSet does not need to be split up any further.
                     True    if the state set requires a split.
        """
        N = len(StateSet)
        assert N != 0, "State set of size '0'. List = " + repr(state_set_list)
        # only one state in state set => no change possible
        if N == 1: return False    

        prototype = self.sm.states[StateSet[0]]

        # loop over all auxiliary states from state set
        non_equivalent_state_list = []
        i = 1
        while i < N:
            state = self.sm.states[StateSet[i]]
            if self.check_equivalence(prototype, state): 
                i += 1             # the next please, ...
            else:
                non_equivalent_state_list.append(state)
                del state_set[i]   # don't increase i since the next canditate shifts to position i
                N -= 1

        if non_equivalent_state_list == []: return False

        # replace state set with the result of the split
        # the old state_set has been adapted by 'split()', only 
        # append the new state set
        self.state_set_list.append(non_equivalent_state_list)
        self.size += 1 

        return True

    def get_index_of_state_set_containing_state(self, StateIdx):
        """Returns the index of the state set that contains the given 
           StateIdx. It returns -1  if no state set contains that index.
        """

        i = -1L   
        for state_set in self.state_set_list:
            i += 1L
            if StateIdx in state_set: return i
        return -1L  

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

            target_0 = self.get_index_of_state_set_containing_state(t0.target_state_index)
            target_1 = self.get_index_of_state_set_containing_state(t1.target_state_index)

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
        i                        = 0
        state_set_list_changed_f = False
        while i < state_set_list.size:
            state_set = state_set_list.get(i)
            
            if state_set_list.split(state_set) == False:  # -- State set remains. 
                i += 1                                    #    The next, please!
            else:                                 # -- No 'i += 1' since deletion shifted 
                state_set_list_changed_f = True   #    the next at the place of i.

            ## print "##", state_set_list.state_set_list

    # If all states in the state sets trigger equivalently, then the state set remains
    # nothing has to be done to the new state_set list, because its by default setup that way 
    return create_state_machine(SM, state_set_list)

def create_state_machine(SM, StateSetList):
    # When the list of state sets did not change, it means that no states inside any
    # state set triggers to a different state set on the same trigger. the state sets can
    # become a new state machine. the state set that contains the initial state becomes 
    # the initial state of the new state machine.   
    state_set_containing_initial_state_i = StateSetList.get_index_of_state_set_containing_state(SM.init_state_index)
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
            target_index = StateSetList.get_index_of_state_set_containing_state(t.target_state_index)
            result.add_transition(start_index, 
                                  t.trigger_set, 
                                  create_state_index(target_index))


        # Merge all core information of the states inside the state set.
        for state_idx in state_set:
            prototype.merge(SM.states[state_idx])

    return result    



