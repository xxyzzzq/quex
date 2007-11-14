# PURPOSE: Regular expressions with a post condition that
#          starts with the same as the end of the core expression
#          are potentially not solveable in the 'classical' way.
#          This module provides functions to detect this case in 
#          a given core and post condition.

def do(CoreStateMachine, PostConditionStateMachine):
    CSM  = CoreStateMachine
    PCSM = PostConditionStateMachine

    assert CSM.__class__.__name__  == "StateMachine"
    assert PCSM.__class__.__name__ == "StateMachine"
    
    core_acceptance_state_list = CSM.get_acceptance_state_list()
    
    assert len(core_acceptance_state_list) == 1 

    for csm_state_idx in core_acceptance_state_list[0]:
        pcsm_state_idx = PCSM.init_state_index

        if  __dive_paths(CSM, CSM.states[csm_state_idx], 
                         PCSM, PCSM.states[pcsm_state_idx]):
            return True

    return False

def __dive_paths(CSM, csm_state, PCSM, pcsm_state):

    csm_transition_list  = csm_state.get_transitions()
    pcsm_transition_list = pcsm_state.get_transitions()

    # If there is no subsequent path in the core or the post condition
    # then we are at a leaf of the tree search. No 'ambigous post condition'
    # has been detected.
    if csm_transition_list == [] or pcsm_transition_list == []:
        return False

    for csm_transition in csm_transition_list:
        for pcsm_transition in pcsm_transition_list:
            # If there is no common character in the transition pair, it does not
            # have to be considered.
            if csm_transition.trigger_set.intersection(pcsm_transition.trigger_set).is_empty():
                continue
            
            # Both trigger on the some same characters.
            #     -----------------------[xxxxxxxxxxxxxxxx]-------------
            #     -------------[yyyyyyyyyyyyyyyyyyyy]-------------------
            #
            # If the target state in the CSM is an acceptance state
            # => The 'ambigous post condition' problem has been detected.
            #    (It means that a valid path in the post condition pattern leads
            #     at the same time to a valid path in the core pattern).
            csm_target_state = CSM.states[csm_transition.target_state_index]
            if csm_target_state.is_acceptance():
                return True
            
            # If the state is not immediately an acceptance state, then
            # search in the subsequent pathes of both state machines.
            pcsm_target_state = PCSM.states[pcsm_transition.target_state_index]
            if __dive_paths(CSM, csm_target_state, PCSM, pcsm_target_state):
                return True

    # None of the investigated paths in the core and post condition leads
    # to an acceptance stage in the core condition. Thus no 'ambigous
    # post condition' can be stated.
    return False
    

