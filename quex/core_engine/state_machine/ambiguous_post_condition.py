# PURPOSE: Quex's strategy to handle post-conditions is the following:
#          When a state is reached that is labeled with 'end of core'
#          it stores the input position in a certain variable. This
#          approach is 'pure' in a sense that it does not circumvent the
#          understanding of a regular expression based state machine.
# 
#          A problem arises with some post-conditions, usually called
#          'dangerous trailing context'. Some of those cases can be 
#          handled by quex. Other's are by nature ambiguous. This
#          file provides functions to analyse the different cases.
# 
# (C) Frank-Rene Schaefer
##############################################################################

from   quex.core_engine.interval_handling import NumberSet, Interval
import quex.core_engine.state_machine.sequentialize as sequentialize
import sys
from   copy import deepcopy


def __assert_state_machines(SM0, SM1):
    assert SM0.__class__.__name__ == "StateMachine"
    assert SM1.__class__.__name__ == "StateMachine"

    
def detect_forward(CoreStateMachine, PostConditionStateMachine):
    """A 'forward ambiguity' denotes a case where the quex's normal
       post condition implementation fails. This happens if an
       iteration in the core pattern is a valid path in the post-
       condition pattern. In this case no decision can be be where
       to reset the input position.

       Example:   x+/x  At the end of the post condition an incoming
                        'x' guides through a path in the post condition
                        and the core pattern. It cannot be determined
                        by a flag where the input position ends.

       NOTE: For many cases where there is a forward ambiguity quex
       can gnerate an inverse post-condition that goes backwards from 
       the end of the post condition (see function 'mount()'). However,
       there are cases where even this is not possible (see function
       'detect_backward()').
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

def detect_backward(CoreStateMachine, PostConditionStateMachine):

    """A 'backward ambiguity' denotes the case where it cannot be clearly be
       determined how far to go back from the end of a post-condition. 
       
       NOTE: This does not mean that the post-condition is ambiguous. Many
       cases that are backward ambiguous can be handled by quex's normal
       post-condition handling.

       Examples:  x/x+   is backward ambiguous because in a stream
                         of 'x' one cannot determine with a pure
                         state machine where to stop. This case,
                         though can be handled by the normal post-
                         condition implementation.

                  x+/x+  is backward ambiguous and cannot be handled
                         by the normal implementation. In fact, this
                         specification does not allow any conclusions
                         about the users intend where to reset the 
                         input after match.
    """

    __assert_state_machines(CoreStateMachine, PostConditionStateMachine)

    my_post_condition_sm = PostConditionStateMachine.clone()

    # (*) Create a modified version of the post condition, where the
    #     initial state is an acceptance state, and no other. This 
    #     allows the detector to trigger on 'iteration'.
    #
    # -- delete all acceptance states in the post condition
    # for state in my_post_condition_sm.states.values():
    #   state.set_acceptance(False)
    # -- set the initial state as acceptance state
    # my_post_condition_sm.get_init_state().set_acceptance(True)

    my_core_sm = CoreStateMachine.get_inverse()
    my_core_sm = my_core_sm.get_DFA()
    my_core_sm = my_core_sm.get_hopcroft_optimization()

    tmp = deepcopy(PostConditionStateMachine)
    # tmp.get_init_state().set_acceptance(True)
    my_post_condition_sm = tmp.get_inverse()
    my_post_condition_sm = my_post_condition_sm.get_DFA()
    my_post_condition_sm = my_post_condition_sm.get_hopcroft_optimization()

    return detect_forward(my_post_condition_sm, my_core_sm)



def __dive_to_detect_iteration(SM0, sm0_state, SM1, sm1_state):
    """This function goes along all path of SM0 that lead to an 
       acceptance state AND at the same time are valid inside SM1.
       The search starts at the states sm0_state and sm1_state.
    """

    sm0_transition_list = sm0_state.get_transitions()
    sm1_transition_list = sm1_state.get_transitions()

    # If there is no subsequent path in SM0 or SM1, 
    # then we are at a leaf of the tree search. No
    # path to acceptance in SM0 lies in SM1.
    if sm0_transition_list == [] or sm1_transition_list == []:
        return False

    for sm0_transition in sm0_transition_list:
        sm0_trigger_set = sm0_transition.trigger_set
        for sm1_transition in sm1_transition_list:
            # If there is no common character in the transition pair, it does not
            # have to be considered.
            sm1_trigger_set = sm1_transition.trigger_set
            intersection = sm0_trigger_set.intersection(sm1_trigger_set)
            if intersection.is_empty():
                continue
            
            # Both trigger on the some same characters.
            #     -----------------------[xxxxxxxxxxxxxxxx]-------------
            #     -------------[yyyyyyyyyyyyyyyyyyyy]-------------------
            #
            # If the target state in the SM0 is an acceptance state,
            # => A valid path in SM1 leads at the same time to along 
            #    valid path in SM0.
            sm0_target_state = SM0.states[sm0_transition.target_state_index]
            if sm0_target_state.is_acceptance():
                return True
            
            # If the state is not immediately an acceptance state, then
            # search in the subsequent pathes of the SM0.
            sm1_target_state = SM1.states[sm1_transition.target_state_index]
            if __dive_to_detect_iteration(SM0, sm0_target_state, SM1, sm1_target_state):
                return True

    # None of the investigated paths in SM0 and SM1 leads to an
    # acceptance state in SM0. 
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
    acceptance_state_list = the_state_machine.get_acceptance_state_list()
    assert len(acceptance_state_list) != 0, \
            "error: mounting pseudo-ambiguous post condition:\n" + \
            "error: no acceptance state in sequentialized state machine."

    # (*) create origin data, in case where there is none yet create new one.
    #     (do not delete, otherwise existing information gets lost)
    for state_idx in acceptance_state_list[0]: 
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
    


