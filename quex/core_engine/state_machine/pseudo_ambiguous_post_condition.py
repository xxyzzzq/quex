# PURPOSE: Regular expressions with a post condition that
#          starts with the same as the end of the core expression
#          are potentially not solveable in the 'classical' way.
#          This module provides functions to detect this case in 
#          a given core and post condition.
from   quex.core_engine.interval_handling import NumberSet, Interval
import quex.core_engine.state_machine.sequentialize as sequentialize
import sys

def detect(CoreStateMachine, PostConditionStateMachine):
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
    
def __get_inverse_state_machine_that_finds_end_of_core_expression(PostConditionSM):
    """In case of a pseudo-ambiguous post condition one needs to go backwards
       in order to search for the end of the core condition. This function 
       creates the inverse state machine that is able to go backwards.

       NOTE: This is a special case, because one already knows that the state
       machine reaches the acceptance state sometime (this is where it actually
       started). That means, that in states other than acceptance states one
       can take out the 'drop out' triggers since they CANNOT occur. This
       enables some speed-up when going backwards.
    """
    result = PostConditionSM.get_inverse()
    result = result.get_DFA()
    result = result.get_hopcroft_optimization()

    # -- delete 'drop-out' transitions in non-acceptance states
    #    NOTE: When going backwards one already knows that the acceptance
    #          stae (the init state of the post condition) is reached, see above.
    for state in result.states.values():
        # -- acceptance states can have 'drop-out' (actually, they need to have)
        if state.is_acceptance(): continue

        state.replace_drop_out_target_states_with_adjacent_targets()

    return result

def mount(the_state_machine, PostConditionSM):
    """This function mounts a post condition to a state machine with
       a mechanism that is able to handle the pseudo ambigous post-
       condition. Note, that this mechanism can also treat 'normal'
       post-conditions. However, it is slightly less efficient.

                core-        post-    
           -----0000000000000111111111--------------

       (1)      |-------------------->
                                     acceptance

       (2)                   <-------|
                             reset input position

       The first step is performed by 'normal' lexing. The second step
       via the backward detector, which is basically an inverse state
       machine of the post-condition.

       NOTE: This function does **not** return a state machine that is
             necessarily deterministic. Run .get_DFA() on the result
             of this function.

       NOTE: This function is very similar to the function that mounts
             a pre-condition to a state machine. The only major difference
             is that the post condition is actually webbed into the 
             state machine for forward lexing. For backward lexing
             a reference is stored that points to the backward detecting
             state machine.
    """
    assert the_state_machine.__class__.__name__ == "StateMachine"
    assert PostConditionSM.__class__.__name__ == "StateMachine"
    # -- state machines with no states are senseless here. 
    assert not the_state_machine.is_empty() 
    assert not PostConditionSM.is_empty()

    # -- trivial pre-conditions should be added last, for simplicity
    # (*) concatinate the two state machines:
    #   -- deletes acceptance states of the core pattern
    #   -- leaves acceptance states of the post condition
    sequentialize.do([the_state_machine, PostConditionSM], MountToFirstStateMachineF=True)

    # (*) get the state machine that can go backwards from the acceptance
    #     state of the post condition to the start of the post-condition.
    #     The start of the post condition is at the same time the end 
    #     of the core pattern.
    backward_detector_sm = __get_inverse_state_machine_that_finds_end_of_core_expression(PostConditionSM)

    # NOTE: We do not need to mark any origins in the backward detector,
    #       since it is not concerned with acceptance states. Its only
    #       task is to reset the input stream.
    # NOTE: It is not necessary that the state machine directly refers to
    #       the backward detector. The origins of the acceptance state will do so.

    # (*) create origin data, in case where there is none yet create new one.
    #     (do not delete, otherwise existing information gets lost)
    for state_idx in the_state_machine.get_acceptance_state_list()[0]:
        state = the_state_machine.states[state_idx]
        if not state.has_origin(): 
            state.add_origin(the_state_machine.get_id(), state_idx)
        state.set_pseudo_ambiguous_post_condition_id(backward_detector_sm.get_id())
        # At the end of the post condition, no input positions are stored.
        # (remember we need to go backwards to set the input position)
        state.set_store_input_position_f(False)

    # We cannot do a NFA to DFA and Hopcroft Optimization, because otherwise we
    # would create a new state machine. This function, though, is considered to 
    # 'mount' something on an existing state machine, i.e. change the object
    # that is referenced by the first argument.
    return the_state_machine
    


