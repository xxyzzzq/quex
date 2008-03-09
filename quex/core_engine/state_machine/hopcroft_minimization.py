from   quex.core_engine.state_machine.core  import StateMachine

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

    def get_state_set_containing_state_index(StateIdx, StateSetList):
        """Returns the index of the state set that contains the given 
           StateIdx. It returns -1  if no state set contains that index.
        """
        i = -1L   
        for state_set in StateSetList:
            i += 1L
            if StateIdx in state_set: return i
        return -1L  
            
    def get_aux_state(StateIdx, StateSetList):
        """Receives: an index of a state and a list of state sets. 
           Creates: a StateInfo-object where the transitions contain
           target indices of the state set, rather the the 'real' target 
           state, i.e. for any transition 't' in the auxiliary state:

                 t.target_state_index = Index of the StateSet, that contains
                                        the original target state in
                                        SM.states[StateIdx]
        """
        assert type(StateIdx) == long

        aux_state = StateInfo()
        for t in SM.states[StateIdx].get_transitions():
            state_set_i = get_state_set_containing_state_index(t.target_state_index, StateSetList)  
            assert state_set_i != -1L, \
                   "target state '" + repr(t.target_state_index) + "' not contained in any state set" + \
                   "state sets = " + repr(StateSetList)
                
            aux_state.add_transition(t.trigger_set, state_set_i)

        aux_state.set_acceptance(SM.states[StateIdx].is_acceptance())
        # add dynamically a new field to the StateInfo object: the original state of the aux state
        aux_state.related_state_idx = StateIdx
        return aux_state

    def split_state_set(AuxliaryStateSet, TriggerSet, TargetIdx):
        """Splits the given StateSet into two sets:
           -- one that contains states that trigger via TriggerSet **only** to TargetIdx, and
           -- one that contains states that trigger via TriggerSet to a different target.
        """ 
        states_that_fit = []
        states_that_do_not_fit = []
        for state in AuxliaryStateSet:
            if state.has_only_one_target_for_trigger_set(TriggerSet, TargetIdx):
                states_that_fit.append(state.related_state_idx)
            else:
                states_that_do_not_fit.append(state.related_state_idx)

        return states_that_fit, states_that_do_not_fit
       
    # (*) main algorithm    
    state_set_list = SM.get_acceptance_state_list(ReturnNonAcceptanceTooF=True,
                                                  SplitAcceptanceStatesByOriginF=True)     
    state_set_list_changed_f = True   
    while state_set_list_changed_f:
        # loop over all sets in state set
        # by default the next state set list ist the same
        state_set_list_changed_f = False

        state_set_i = -1
        for state_set in state_set_list:
            state_set_i += 1
            
            N = len(state_set)
            assert N != 0, \
                   "state set of size '0' occured\n" + \
                   "state sets = " + repr(state_set_list)

            if N == 1:
                # only one state in state set => no change possible
                continue    
            # auxiliary states: an auxiliary state 'i' triggers to the state_set 'k' if 
            #                   the original state 'i' triggered to a target state belonging
            #                   to state set 'k'. (target-index = state set to which the
            #                   original target belongs).
            # NOTE: An auxiliary state contains an extra field: related_state_idx that
            #       contains the index as it appears in the state set and in SM.states.
            aux_states = map(lambda x: get_aux_state(x, state_set_list), state_set)

            # -- sort the auxiliary state, so that aux states with only an epsilon transition
            #    come last. this way we ensure that they are checked against all normal transitions
            #    and no trigger sets considerations for epsilon transitions have to be made.
            aux_states.sort(lambda x, y: - cmp(len(x.get_transitions()), len(y.get_transitions())))
    
            # loop over all auxiliary states from state set
            for i in range(N):
                # check for all a transitions: does a state in the same state set trigger
                # on the same trigger to a different state set?
                other_index_list = filter(lambda k: k != i, range(N))
                other_aux_states = map(lambda k: aux_states[k], other_index_list)
                for t in aux_states[i].get_transitions():
                    # split the auxiliary states in those that trigger on t.trigger_set to t.target_state_index
                    # and those that do not. If the second set, i.e. the set of stats that do not is non-empty
                    # then there are states that behave unequivalent, and we need to split the state set.
                    set_of_fit_states, set_of_others = split_state_set(other_aux_states, 
                                                                       t.trigger_set, t.target_state_index)     
                    if set_of_others != []: 
                        set_of_fit_states += [ aux_states[i].related_state_idx ]   # add the currently considered state, of course
                        # replace the currently considered state set by the 'split-up' 
                        del state_set_list[state_set_i]
                        state_set_list.extend([set_of_fit_states, set_of_others])
                        state_set_list_changed_f = True
                        # state set list has changed, return to lowest loop level
                        break
                if state_set_list_changed_f: break
            if state_set_list_changed_f: break
            # if all states in the state sets trigger equivalently, then the state set remains
            # nothing has to be done to the new state_set list, because its by default setup that way 

        # next run with newly configured state set list

    # when the list of state sets did not change, it means that no states inside any
    # state set triggers to a different state set on the same trigger. the state sets can
    # become a new state machine. the state set that contains the initial state becomes 
    # the initial state of the new state machine.   
    state_set_containing_initial_state_i = get_state_set_containing_state_index(SM.init_state_index, 
                                                                                state_set_list)
    map_new_state_index = {}
    def get_new_state_index(state_set_index):
        if not map_new_state_index.has_key(state_set_index):
            map_new_state_index[state_set_index] = state_machine_index.get()
        return map_new_state_index[state_set_index]
                
    result = StateMachine(get_new_state_index(state_set_containing_initial_state_i),
                          PreConditionStateMachine          = SM.pre_condition_state_machine, 
                          TrivialPreConditionBeginOfLineF   = SM.has_trivial_pre_condition_begin_of_line())

    # build up the state machine out of the auxiliary states
    state_set_idx = -1L
    for state_set in state_set_list:
        state_set_idx += 1L
        assert state_set != [], \
               "state set of size '0' occured\n" + \
               "state sets = " + repr(state_set_list)

        # states in one set behave all equivalent with respect to target state sets
        # thus only one state from the start set has to be considered.      
        # NOTE: the target_state_index of an auxiliary state contains the index
        #       of a state set.           
        aux_state = get_aux_state(state_set[0], state_set_list)
        start_index = get_new_state_index(state_set_idx)
        if result.has_start_state_index(start_index) == False:
            result.create_new_state(StateIdx=start_index)

        # if state set contains an acceptance state, then the result is 'acceptance'
        # (NOTE: if some state in a state set where 'acceptance' states and others not,
        #        then the state sets where not equivalence classes. Thus checking one
        #        state in the set is enough. anyway the initial sets are splitted according
        #        to acceptance.)        
        result.set_acceptance(start_index, aux_state.is_acceptance())

        for t in aux_state.get_transitions():
            result.add_transition(start_index, 
                                  t.trigger_set, 
                                  get_new_state_index(t.target_state_index))


        # tracing the origins
        for state_idx in state_set:
            result.states[start_index].add_origin_list(SM.states[state_idx].get_origin_list(),
                                                       StoreInputPositionFollowsAcceptanceF=False)

    return result    


def split_states(SM):
    """Returns the set of states that are 'acceptance'. If the optional     
       argument 'ReturnNonAcceptanceTooF' is specified, then the non-
       acceptance states are also returned.

    """   
    def __criteria(state):
        return state.is_acceptance()

    acceptance_state_list     = []
    non_acceptance_state_list = []
    for state_idx, state in self.states.items():
        if state.is_acceptance(): acceptance_state_list.append(state_idx)
        else:                     non_acceptance_state_list.append(state_idx)

    # map: set of original states ---> state indices that are of this origin
    sorter_dict = {}   
    def sorter_dict_add(key, list_element):
        if sorter_dict.has_key(key): sorter_dict[key].append(list_element)
        else:                        sorter_dict[key] = [ list_element ]                             

    for state_index in acceptance_state_list:
        origin_state_machine_ids = map(lambda origin: 
                                    origin.state_machine_id, 
                                    self.states[state_index].get_origin_list())
        state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
        sorter_dict_add(state_combination_id, state_index)

    # each 'value' (belonging to a key) represents the set of states that have the
    # same combination of original states
    result = sorter_dict.values()
        
    if non_acceptance_state_list != []: 
        return result + [ non_acceptance_state_list ]
            
    return result

