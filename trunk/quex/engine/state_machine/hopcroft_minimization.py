import quex.engine.state_machine.index as     state_machine_index
from   quex.engine.state_machine.core  import StateMachine
from   quex.engine.state_machine.index import map_state_combination_to_index
from   itertools import islice, ifilter

class StateSet_List:
    def __init__(self, StateMachine):
        self.sm = StateMachine
        #
        # -- map: state index --> index of the state set that contains it
        self.map = {} 
        #
        # -- create: self.state_set_list by initial split of all states.
        self.__todo = set([])
        self.size   = 0
        self.__initial_split()

    def todo_list(self):
        return list(self.__todo)

    def pre_split(self, StateSetIndex):
        """Separate state_set into two state sets:
           (1) The set of states that have the same target state sets,
               as a arbitrarily chosen prototype := 'harmonic'.
           (2) Those who differ from the prototype.

           The state set that matches the prototype can be considered 
           'harmonic' since it triggers for sure to the same target
           state sets. The prototype is packed into a separate state
           set. The other states remain in the old state set. 

           If there was a prototype that separated the set then the
           what does not match the prototype is possibly not-harmonic.

           RETURNS: True  Split happened.
                          The old state set is possible non-harmonic.
                    False No split happened.
                          The old state set and the prototype are
                          identical.
        """
        def get_target_state_set_list(StateIndex):
            state = self.sm.states[StateIndex]
            target_list = state.transitions().get_map().iterkeys()
            return set([self.map[i] for i in target_list])

        state_set = self.state_set_list[StateSetIndex]
        prototype = get_target_state_set_list(state_set[0])

        match_set = [ state_set[0] ] 
        for state_index in islice(state_set, 1, None):
            if prototype == get_target_state_set_list(state_index): 
                match_set.append(state_index)

        if len(match_set) == len(state_set): return False

        # Cut the matching set and put it into a separate one
        for state_index in match_set:
            del state_set[state_set.index(state_index)]

        # len(match_set) == 1 => not added to __todo
        self.__add_state_set(match_set)
        if len(state_set) == 1: self.__todo.remove(StateSetIndex)

        return True

    def harmonize(self):
        """Splits the given state set into state sets that contain only 
           states that transits to the same set of target state sets.
        """
        change_f = True
        while change_f:
            change_f = False
            for i in list(self.__todo):
                if self.pre_split(i):
                    change_f = True
            
    def split(self, StateSetIndex):
        """RETURNS:  False   if StateSet does not need to be split up any further.
                     True    if the state set requires a split.
        """
        state_set = self.state_set_list[StateSetIndex]
        #
        N         = len(state_set)
        assert N != 0, "State set of size '0'. List = " + repr(state_set_list)
        # only one state in state set => no change possible
        if N == 1: 
            self.__todo.remove(StateSetIndex)
            return False    

        def normalized_map(DB):
            result = {}
            for target_index, trigger_map in DB.iteritems():
                # Target in terms of equivalent state sets
                target = self.map[target_index]
                entry  = result.get(target)
                if entry == None: entry = trigger_map 
                else:             entry = entry.union(trigger_map)
                result[target] = entry
            return result

        # -- choose one arbitrary state (for example state 0) as a prototype
        #    which is compared against the remaining states in the state set.
        prototype_index  = state_set[0]
        remainder        = islice(state_set, 1, None)

        prototype            = self.sm.states[prototype_index]
        prototype_map        = normalized_map(prototype.transitions().get_map())
        equivalent_state_set = [ prototype_index ] 

        if len(prototype_map) == 0:
            # If there are no target states, then there can be no split.
            # The state set is done.
            self.__todo.remove(StateSetIndex)
            return False

        # Since all state sets are 'harmonized' at the entry of this function
        # It can be assumed that the prototype contains all target_set indices
        # Loop over all remaining states from state set
        for state_index in remainder:
            state = self.sm.states[state_index]
            state_map = normalized_map(state.transitions().get_map())
            for target in prototype_map.iterkeys():
                if not prototype_map[target].is_equal(state_map[target]): break
            else:
                equivalent_state_set.append(state_index)

        if len(equivalent_state_set) == N:
            assert N != 1 # See function entry,
            # Thus: self.__todo.remove(...) not necessary.
            if self.__todo.isdisjoint(list(prototype_map.iterkeys())):
                self.__todo.remove(StateSetIndex)
            return False

        i = self.__add_state_set(equivalent_state_set)
        # If len(equivalent_state_set) == 1, then it is not added to __todo
        # Thus: self.__todo.remove(...) not necessary.
        if i != -1 and self.__todo.isdisjoint(list(prototype_map.iterkeys())):
            self.__todo.remove(i)

        # -- States that are not equivalent (probably most likely) remain in the 
        #    original state set and the ones that are equivalent are put into a new
        #    set at the end of the state set list.
        #    
        #    Delete equivalent states from the original state set
        for state_index in equivalent_state_set:
            i = state_set.index(state_index)
            del state_set[i]

        if len(state_set) == 1 and StateSetIndex in self.__todo: 
            self.__todo.remove(StateSetIndex)

        return True

    def __initial_split(self):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

        """   
        self.state_set_list = []

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
        def db_add(key, state_index):
            if db.has_key(key): db[key].append(state_index)
            else:               db[key] = [ state_index ]                             

        for state_index in ifilter(lambda x: x not in non_acceptance_state_set, self.sm.states.iterkeys()): 
            state = self.sm.states[state_index]
            origin_state_machine_ids = map(lambda origin: origin.state_machine_id, 
                                           state.origins())
            state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
            db_add(state_combination_id, state_index)

        # (2b) Enter the split acceptance state sets.
        for state_set in db.values():
            self.__add_state_set(state_set)

    def __add_state_set(self, NewStateSet):
        """RETURNS: N >= 0 index of the new state set, if it is added to 
                           the todo list
                    - 1    if the new state set is not added to the todo list.
        """
        #    Create the new state set at the end of the list
        self.state_set_list.append(NewStateSet)
        # -- Mark in the map the states that have moved to the new state set at the end.
        for state_index in NewStateSet:
            self.map[state_index] = self.size

        # -- increase the size counter
        self.size += 1 

        # -- Index of the last state set = size - 1
        # if not DoneF: self.__todo.add(self.size)
        if len(NewStateSet) != 1: 
            self.__todo.add(self.size - 1)
            return self.size - 1
        else:
            return -1

DEBUG_F = True

def do(SM, CreateNewStateMachineF=True):
    """Reduces the number of states according to equivalence classes of states. It starts
       with two sets: 
       
            (1) the set of acceptance states, 
                -- these states need to be splitted again according to their origin.
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
    global DEBUG_F
    if DEBUG_F:
        state_index_set = set(SM.states.iterkeys())

    # (*) main algorithm ________________________________________________________________    
    state_set_list = StateSet_List(SM)

    state_set_list_changed_f = True   
    while state_set_list_changed_f:
        # Loop over all sets in state set
        # by default the next state set list is the same
        state_set_list.harmonize()

        state_set_list_changed_f = False
        for i in state_set_list.todo_list():
            if state_set_list.split(i):           
                state_set_list_changed_f = True   # split happened, state sets changed.
                break
    # ___________________________________________________________________________________

    if DEBUG_F:
        assert state_index_set == set(SM.states.iterkeys())
        mentioned_state_index_set = set()
        for state_set in state_set_list.state_set_list:
            assert mentioned_state_index_set.isdisjoint(state_set)
            mentioned_state_index_set.update(state_set)
        assert state_index_set == mentioned_state_index_set

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
        for target_state_index, trigger_set in prototype.transitions().get_map().iteritems():
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
    for dummy in ifilter(lambda state_set: len(state_set) != 1, StateSetList.state_set_list):
        break
    else:
        return sm
    
    # We know, that all states in a state set are equivalent. Thus, all but one
    # of each set can be thrown away.
    replacement_dict = {}
    for state_set in StateSetList.state_set_list:
        if len(state_set) == 1: continue

        # Merge all core information of the states inside the state set.
        prototype_index = state_set[0]
        prototype       = sm.states[prototype_index]
        for state_idx in islice(state_set, 1, None):
            prototype.merge(sm.states[state_idx])
            # The prototype takes over the role of all
            replacement_dict[state_idx] = prototype_index

        for state_idx in islice(state_set, 1, None):
            del sm.states[state_idx]

    # Replace the indices of the thrown out states
    if replacement_dict.has_key(sm.init_state_index):
       sm.init_state_index = replacement_dict[sm.init_state_index]
    
    for state in sm.states.itervalues():
       state.transitions().replace_target_indices(replacement_dict)

    return sm    

