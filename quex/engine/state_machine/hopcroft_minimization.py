import quex.engine.state_machine.index as     state_machine_index
from   quex.engine.state_machine.core  import StateMachine
from   quex.engine.state_machine.index import map_state_combination_to_index
from   itertools import islice, ifilter
from   operator  import attrgetter

class StateSet_List:
    def __init__(self, StateMachine):
        self.sm = StateMachine
        #
        # -- map: [state index]  -->  [index of the state set that contains it]
        self.map = {} 
        #
        # -- create: self.state_set_list by initial split of all states.
        self.size           = 0
        self.state_set_list = []
        self.__todo         = set()
        self.__initial_split()
        self.size = len(self.state_set_list)

    def todo(self):
        return self.__todo

    def get(self, Index):
        return self.state_set_list[Index]

    def group(self, StateSet):
        """Group states in state set according to the target state sets."""
        result = {}
        for state in [self.sm[i] for i in StateSet]:
            db = state.transitions().get_map()
            target_set_index_list = tuple(set([self.map[i] for i in db.iterkeys()]))
            # What target combination is triggered by what state?
            result.setdefault(target_set_index_list, []).append(state_index)
        return result

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
        if len(state_set) > 25:
            prototype_index  = min(state_set, key=lambda x: len(self.sm.states[x].transitions().get_map()))
            remainder        = ifilter(lambda x: x != prototype_index, state_set)
        else:
            prototype_index  = state_set[0]
            remainder        = islice(state_set, 1, None)

        prototype            = self.sm.states[prototype_index]
        equivalent_state_set = [ prototype_index ] 

        # -- loop over all remaining states from state set
        i         = 1   # state_set[i] = state index
        element_n = N   # remaining number of elements in state set

        def normalized_map(DB, ReferenceSet=None, Size=None):
            result = {}
            if ReferenceSet is None:
                for target_index, trigger_map in DB.iteritems():
                    # Target in terms of equivalent state sets
                    target = self.map[target_index]
                    result.setdefault(target, []).append(trigger_map)
            else:
                for target_index, trigger_map in DB.iteritems():
                    # Target in terms of equivalent state sets
                    target = self.map[target_index]
                    if target not in ReferenceSet: return None
                    result.setdefault(target, []).append(trigger_map)
                if len(result) != Size: return None

            for target, trigger_map_list in result.items():
                if len(trigger_map_list) == 1: 
                    result[target] = trigger_map_list[0]
                else:
                    union = trigger_map_list[0].union(trigger_map_list[1])
                    for trigger_set in islice(trigger_map_list, 2, None):
                        union.unite_with(trigger_set)
                    result[target] = union
            return result

        prototype_map = normalized_map(prototype.transitions().get_map())
        prototype_set = prototype_map.keys()
        Size          = len(prototype_set)
        for state_index in remainder:
            state = self.sm.states[state_index]
            state_map = normalized_map(state.transitions().get_map(), prototype_set, Size)
            if state_map is None: 
                continue
            for target in prototype_set:
                if not prototype_map[target].is_equal(state_map[target]): break
            else:
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

        self.__add_state_set(equivalent_state_set)
        return True

    def __initial_split(self):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

        """   

        # (1) Split according to acceptance and non-acceptance
        non_acceptance_state_set = []
        for state_index, state in ifilter(lambda x: not x[1].is_acceptance(), self.sm.states.iteritems()):
            non_acceptance_state_set.append(state_index) 

        # NOTE: Under normal conditions, there **must** be at least one non-acceptance state,
        #       which happens to be the initial state (otherwise nothing would be acceptable).
        #       But: The minimization might be called for sub-patterns such as 'a*' which
        #       actually allow the first state to be acceptance.
        if len(non_acceptance_state_set) != 0: 
            self.__add_state_set(non_acceptance_state_set)

        # BUT: There should always be at least one acceptance state.
        assert len(self.sm.states) - len(non_acceptance_state_set) != 0

        # (2) Split the acceptance states according to their origin. An acceptance
        #     state maching the, for example, an identifier is not equivalent an 
        #     acceptance state thate that matches a number.
        db = {}   
        for state_index in ifilter(lambda i: i not in non_acceptance_state_set, self.sm.states.iterkeys()):
            state = self.sm.states[state_index]
            relevant_origins = filter(lambda origin: origin.store_input_position_f() or origin.is_acceptance(),
                                      state.origins())

            origin_state_machine_ids = []
            for origin in sorted(relevant_origins, key=attrgetter("state_machine_id")):
                origin_state_machine_ids.append(origin.state_machine_id)
                if origin.pre_context_id() == -1 and not origin.pre_context_begin_of_line_f():
                    # First unconditional acceptance dominates the test
                    break
            # BETTER: state_combination_id = tuple(origin_state_machine_ids) 
            # BUT:    unit tests need to be adapted
            state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
            db.setdefault(state_combination_id, []).append(state_index)

        # (2b) Enter the split acceptance state sets.
        for state_set in db.values():
            self.__add_state_set(state_set)

    def __add_state_set(self, NewStateSet):
        #    Create the new state set at the end of the list
        self.state_set_list.append(NewStateSet)
        # -- Mark in the map the states that have moved to the new state set at the end.
        for state_index in NewStateSet:
            self.map[state_index] = self.size
        # -- increase the size counter
        self.__todo.add(self.size)
        self.size += 1 

        return True

def do(SM, CreateNewStateMachineF=True):
    """Reduces the number of states according to equivalence classes of states. It starts
       with two sets: 
       
            (1) the set of acceptance states, 
                -- these states need to be split again according to their origin.
                   Acceptance of state machine A is not equal to acceptance of 
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
        while i < state_set_list.size:
            if state_set_list.split(i):           
                state_set_list_changed_f = True   # -- a split happened, the state sets changed ...  
            i += 1

    # If all states in the state sets trigger equivalently, then the state set remains
    # nothing has to be done to the new state_set list, because its by default setup that way 
    if CreateNewStateMachineF: return create_state_machine(SM, state_set_list)
    else:                      return adapt_state_machine(SM, state_set_list)

def create_state_machine(SM, StateSetList):
    # If all states are of size one, this means, that there were no states that
    # could have been combined. In this case a simple copy of the original
    # state machine will do.
    if len(filter(lambda state_set: len(state_set) != 1, StateSetList.state_set_list)) == 0:
        return SM.clone()
    
    # Define a mapping from the state set to a new target state index
    map_new_state_index = {}
    for state_set_index in range(len(StateSetList.state_set_list)):
        map_new_state_index[state_set_index] = state_machine_index.get()
                
    # The state set that contains the initial state becomes the initial state of 
    # the new state machine.   
    state_set_containing_initial_state_i = StateSetList.map[SM.init_state_index]
    result = StateMachine(map_new_state_index[state_set_containing_initial_state_i],
                          Core = SM.core())

    # Ensure that each target state index has a state inside the state machine
    for new_state_index in map_new_state_index.values():
        result.create_new_state(StateIdx=new_state_index)

    # Build up the state machine out of the remaining state sets
    state_set_idx = -1L
    for state_set in StateSetList.state_set_list:
        state_set_idx += 1L
        assert len(state_set) != 0, "State set of size '0'. List = " + repr(StateSetList)

        # The prototype: States in one set behave all equivalent with respect to target state sets
        # thus only one state from the start set has to be considered.      
        prototype    = SM.states[state_set[0]]
        # The representive: shall represent the state set in the new state machine.
        representive = result.states[map_new_state_index[state_set_idx]]

        # The representive must have all transitions that the prototype has
        for target_state_index, trigger_set in prototype.transitions().get_map().items():
            target_state_set_index = StateSetList.map[target_state_index]
            representive.add_transition(trigger_set, 
                                        map_new_state_index[target_state_set_index])

        # Merge all core information of the states inside the state set.
        # If one state set contains an acceptance state, then the result is 'acceptance'.
        # (Note: The initial split separates acceptance states from those that are not
        #  acceptance states. There can be no state set containing acceptance and 
        #  non-acceptance states) 
        # (Note, that the prototype's info has not been included yet, consider whole set)
        for state_idx in state_set:
            representive.merge(SM.states[state_idx])

    return result    

def adapt_state_machine(sm, StateSetList):
    # If all states are of size one, this means, that there were no states that
    # could have been combined. In this case nothing is to be done.
    if len(filter(lambda state_set: len(state_set) != 1, StateSetList.state_set_list)) == 0:
        return sm
    
    # We know, that all states in a state set are equivalent. Thus, all but one
    # of each set can be thrown away.
    replacement_dict = {}
    for state_set in StateSetList.state_set_list:
        if len(state_set) == 1: continue

        # Merge all core information of the states inside the state set.
        prototype_index = state_set[0]
        prototype       = sm.states[state_set[0]]
        for state_idx in state_set[1:]:
            prototype.merge(sm.states[state_idx])

        # Throw the meaningless states away. Transitions to them need to 
        # point to the prototype
        for state_index in state_set[1:]:
            replacement_dict[state_index] = prototype_index
            del sm.states[state_index]

    # Replace the indices of the thrown out states
    if replacement_dict.has_key(sm.init_state_index):
       sm.init_state_index = replacement_dict[sm.init_state_index]
    
    for state in sm.states.values():
       state.transitions().replace_target_indices(replacement_dict)

    return sm    


