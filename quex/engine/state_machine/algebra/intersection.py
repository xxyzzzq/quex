from   quex.engine.state_machine.core                 import StateMachine, State
from   quex.engine.state_machine.index                import map_state_combination_to_index
import quex.engine.state_machine.algorithm.beautifier as     beautifier
import quex.engine.state_machine.algebra.reverse      as     reverse

def do(SM_List):
    reverse_sm_list          = [ reverse.do(sm)                            for sm in SM_List ]
    state_id_set_list        = [ set(sm.states.iterkeys())                 for sm in reverse_sm_list ]
    acceptance_state_id_list = [ set(sm.get_acceptance_state_index_list()) for sm in reverse_sm_list ]

    def has_one_from_each(StateIDSet_List, StateIDSet):
        """StateIDSet_List[i] is the set of state indices from state 
        machine 'i' in 'reverse_sm_list'. 

        RETURNS: True -- If the StateIDSet has at least one state 
                         from every state machine.
                 False -- If there is at least one state machine 
                          that has no state in 'StateIDSet'.
        """
        for state_id_set in StateIDSet_List:
            if state_id_set.isdisjoint(StateIDSet): 
                return False
        return True

    # Plain merge of all states of all state machines with an 
    # epsilon transition from the init state to all init states
    # of the reverse_sm
    for rsm in reverse_sm_list:
        sm.states.update(rsm.states)
        sm.add_epsilon_transition(sm.init_state_index, rsm.init_state_index) 

    initial_state_epsilon_closure = sm.get_epsilon_closure(sm.init_state_index) 

    InitState = State.new_merged_core_state(sm.states[i] for i in initial_state_epsilon_closure)
    result    = StateMachine(InitState=InitState)

    # (*) prepare the initial worklist
    worklist = [ ( result.init_state_index, initial_state_epsilon_closure) ]

    epsilon_closure_db = sm.get_epsilon_closure_db()

    while len(worklist) != 0:
        # 'start_state_index' is the index of an **existing** state in the state machine.
        # It was either created above, in StateMachine's constructor, or as a target
        # state index.
        start_state_index, start_state_combination = worklist.pop()
 
        # (*) compute the elementary trigger sets together with the 
        #     epsilon closure of target state combinations that they trigger to.
        #     In other words: find the ranges of characters where the state triggers to
        #     a unique state combination. E.g:
        #                Range        Target State Combination 
        #                [0:23]   --> [ State1, State2, State10 ]
        #                [24:60]  --> [ State1 ]
        #                [61:123] --> [ State2, State10 ]
        #
        elementary_trigger_set_infos = sm.get_elementary_trigger_sets(start_state_combination,
                                                                      epsilon_closure_db)
        ## DEBUG_print(start_state_combination, elementary_trigger_set_infos)

        # (*) loop over all elementary trigger sets
        for epsilon_closure_of_target_state_combination, trigger_set in elementary_trigger_set_infos.iteritems():
            #  -- if there is no trigger to the given target state combination, then drop it
            if trigger_set.is_empty(): 
                continue
            elif not has_one_from_each(state_id_set_list, epsilon_closure_of_target_state_combination):
                continue

            # -- add a new target state representing the state combination
            #    (if this did not happen yet)
            target_state_index = \
                 map_state_combination_to_index(epsilon_closure_of_target_state_combination)

            # -- if target state combination was not considered yet, then create 
            #    a new state in the state machine
            if not result.states.has_key(target_state_index):
                # create the new target state in the state machine
                # Accept only if all accept.
                acceptance_f = has_one_from_each(acceptance_state_id_list, 
                                                 epsilon_closure_of_target_state_combination)
                result.states[target_state_index] = State(AcceptanceF = acceptance_f, 
                                                          StateIndex  = target_state_index)

                worklist.append((target_state_index, epsilon_closure_of_target_state_combination))  

            # -- add the transition 'start state to target state'
            result.add_transition(start_state_index, trigger_set, target_state_index)

    if not result.has_acceptance_states():
        return StateMachine()
    else:
        return beautifier.do(reverse.do(result))
