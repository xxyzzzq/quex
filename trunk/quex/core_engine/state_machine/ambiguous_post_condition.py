# PURPOSE: Regular expressions with a post condition that
#          starts with the same as the end of the core expression
#          are potentially not solveable in the 'classical' way.
#          This module provides functions to detect this case in 
#          a given core and post condition.
from   quex.core_engine.interval_handling import NumberSet, Interval
import quex.core_engine.state_machine.sequentialize as sequentialize
import sys


def __assert_state_machines(SM0, SM1):
    assert SM0.__class__.__name__ == "StateMachine"
    assert SM1.__class__.__name__ == "StateMachine"

    
def detect_total(CoreStateMachine, PostConditionStateMachine):
    """A post condition, where there is an possible iteration
       starting from end of the core pattern inside both
       state machines is TOTALLY AMBIGUOUS! For Example:  x+/x+
       Is totally ambiguous since in the general case no judgement
       can be made about the end of the core pattern, so the 
       input position cannot be reset appropriately.
    
       Detect an iteration to the BEGINNING of a post condition 
       while remaining on a valid path of the core pattern.
    """

    __assert_state_machines(CoreStateMachine, PostConditionStateMachine)

    my_post_condition_sm = PostConditionStateMachine.clone()

    # (*) Create a modified version of the post condition, where the
    #     initial state is an acceptance state, and no other. This 
    #     allows the detector to trigger on 'iteration'.
    #
    # -- delete all acceptance states in the post condition
    for state in my_post_condition_sm.states.values():
       state.set_acceptance(False)
    # -- set the initial state as acceptance state
    my_post_condition_sm.get_init_state().set_acceptance(True)
    
    core_acceptance_state_list = CoreStateMachine.get_acceptance_state_list()
    assert len(core_acceptance_state_list) == 1 

    my_pcsm_init_state = my_pcsm_init_state.get_init_state()
    for csm_state_idx in core_acceptance_state_list[0]:
        csm_state = CoreStateMachine.states[csm_state_idx]
        if  __dive_to_detect_iteration(my_post_condition_sm, my_pcsm_init_state, 
                                       CoreStateMachine,     csm_states):
            return True

    return False


def detect_pseudo(CoreStateMachine, PostConditionStateMachine):
    """A pseudo ambiguous post condition is what is called in flex
       a 'dangeruous trailing context'. An expression x*/x allows
       to reset the input position propperly, since the length of the
       post conditional pattern can be known. This happesn through 
       inversion of the post condition state machine and then going
       backwards. A mismatch will end the 'diving' into the core
       pattern. NOTE: This diving into the core pattern is not 
       prevented if iterations in the post condition state machine
       match with iterations in the core pattern. For this reason,
       after a call to this function, ensure that the two 
       patterns are not totally ambiguous using the function above.
    """
    __assert_state_machines(CoreStateMachine, PostConditionStateMachine)
    
    core_acceptance_state_list = CoreStateMachine.get_acceptance_state_list()
    assert len(core_acceptance_state_list) == 1 

    pcsm_init_state = PostConditionStateMachine.get_init_state()
    for csm_state_idx in core_acceptance_state_list[0]:
        csm_state = CoreStateMachine.states[csm_state_idx]
        if  __dive_to_detect_iteration(CoreStateMachine,          csm_state, 
                                       PostConditionStateMachine, pcsm_init_state):
            return True

    return False

def __dive_to_detect_iteration(SM0, sm0_state, SM1, sm1_state):
    """This function goes along all path of SM0 that lead to an 
       acceptance state AND at the same time are valid inside SM1.
       The search starts at the states sm0_state and sm1_state.
    """

    sm0_transition_list = sm0_state.get_transitions()
    sm1_transition_list = sm1_state.get_transitions()

    # If there is no subsequent path in the core or the post condition
    # then we are at a leaf of the tree search. No 'ambigous post condition'
    # has been detected.
    if sm0_transition_list == [] or sm1_transition_list == []:
        return False

    for sm0_transition in sm0_transition_list:
        for sm1_transition in sm1_transition_list:
            # If there is no common character in the transition pair, it does not
            # have to be considered.
            if sm0_transition.trigger_set.intersection(sm1_transition.trigger_set).is_empty():
                continue
            
            # Both trigger on the some same characters.
            #     -----------------------[xxxxxxxxxxxxxxxx]-------------
            #     -------------[yyyyyyyyyyyyyyyyyyyy]-------------------
            #
            # If the target state in the SM0 is an acceptance state
            # => The 'ambigous post condition' problem has been detected.
            #    (It means that a valid path in the post condition pattern leads
            #     at the same time to a valid path in the core pattern).
            sm0_target_state = SM0.states[sm0_transition.target_state_index]
            if sm0_target_state.is_acceptance():
                return True
            
            # If the state is not immediately an acceptance state, then
            # search in the subsequent pathes of the SM0.
            sm1_target_state = SM1.states[sm1_transition.target_state_index]
            if __dive_to_detect_iteration(SM0, sm0_target_state, SM1, sm1_target_state):
                return True

    # None of the investigated paths in the core and post condition leads to an
    # acceptance state in SM0. Thus no 'ambigous post condition' can be stated.
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

    # -- delete 'drop-out' transitions in non-acceptance states
    #    NOTE: When going backwards one already knows that the acceptance
    #          stae (the init state of the post condition) is reached, see above.
    for state in result.states.values():
        # -- acceptance states can have 'drop-out' (actually, they need to have)
        if state.is_acceptance(): continue

        state.replace_drop_out_target_states_with_adjacent_targets()

    result = result.get_DFA()
    result = result.get_hopcroft_optimization()

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
    


