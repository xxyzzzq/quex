#! /usr/bin/env python
import sys
from copy import deepcopy
sys.path.append("../")

from quex.core_engine.state_machine.core import *
import quex.core_engine.state_machine.ambiguous_post_condition as apc


def do(the_state_machine, post_condition_sm, DEMONSTRATION_TurnOffSpecialSolutionF=False):
    """ Appends a post condition to the given state machine. This process is very
        similar to sequentialization. There is a major difference, though:
       
        Given a state machine (e.g. a pattern) X with a post condition Y, 
        a match is only valid if X is followed by Y. Let Xn be an acceptance
        state of X and Ym an acceptance state of Y: 

               ---(Xn-1)---->(Xn)---->(Y0)----> ... ---->((Ym))
                             store                       acceptance
                             input
                             position
        
        That is, it holds:

           -- The next input position is stored the position of Xn, even though
              it is 'officially' not an acceptance state.

           -- Ym will be an acceptance state, but it will not store 
              the input position!       

        The analysis of the next pattern will start at the position where
        X stopped, even though Ym is required to state acceptance.    
       
    """
    # (*) do some consistency checking   
    if the_state_machine.__class__.__name__ != "StateMachine":
        raise "expected 1st argument as objects of class StateMachine\n" + \
              "received: " + the_state_machine.__class__.__name__
    if post_condition_sm.__class__.__name__ != "StateMachine":
        raise "expected 2nd argument as objects of class StateMachine\n" + \
              "received: " + post_condition_sm.__class__.__name__

    if the_state_machine.is_post_conditioned():
        raise "post conditioned state machine cannot be post-conditioned again."

    # -- state machines with no states are senseless here. 
    if the_state_machine.is_empty():
        raise "empty state machine can have no post condition"
    if post_condition_sm.is_empty():
        raise "empty state machine cannot be a post-condition"

    # -- a post condition with an initial state that is acceptance is not
    #    really a 'condition' since it accepts anything. The state machine remains
    #    un-post conditioned.
    if post_condition_sm.get_init_state().is_acceptance():
        print "warning: post condition accepts anything---replaced by no post condition."
        the_state_machine.mark_state_origins()
        return the_state_machine
    
    # (*) Two ways of handling post-conditions:
    #
    #     -- Seldom Exception: 
    #        Pseudo-Ambiguous Post Conditions (x+/x) -- detecting the end of the 
    #        core pattern after the end of the post condition
    #        has been reached.
    #
    if not DEMONSTRATION_TurnOffSpecialSolutionF:
        if apc.detect_forward(the_state_machine, post_condition_sm):
            if apc.detect_backward(the_state_machine, post_condition_sm):
                # -- for post conditions that are forward and backward ambiguous
                #    a philosophical cut is necessary.
                post_condition_sm = apc.philosophical_cut(the_state_machine, post_condition_sm)
            apc.mount(the_state_machine, post_condition_sm)
            return the_state_machine

        
    #     -- The 'normal' way: storing the input position at the end of the core
    #        pattern.
    #
    # (*) need to clone the state machines, i.e. provide their internal
    #     states with new ids, but the 'behavior' remains. This allows
    #     state machines to appear twice, or being used in 'larger'
    #     conglomerates.
    result     = the_state_machine
    post_clone = post_condition_sm.clone() 
    #     origins of the post condition are **irrelevant**
    post_clone.delete_state_origins()

    # (*) collect all transitions from both state machines into a single one
    #
    #     NOTE: The start index is unique. Therefore, one can assume that each
    #           clone_list '.states' dictionary has different keys. One can simply
    #           take over all transitions of a start index into the result without
    #           considering interferences (see below)
    #
    orig_acceptance_state_id_list = result.get_acceptance_state_list()[0]

    # -- mount on every acceptance state the initial state of the following state
    #    machine via epsilon transition
    result.mount_to_acceptance_states(post_clone.init_state_index, 
                                      CancelStartAcceptanceStateF = True)
    for start_state_index, states in post_clone.states.items():        
        result.states[start_state_index] = deepcopy(states)

    # -- make sure that for each state a origin information is present 
    # result.mark_state_origins(DontMarkIfOriginsPresentF=True)

    # -- consider the pre-condition, it has to be moved to the acceptance state
    pre_condition_sm_id= -1L
    if the_state_machine.pre_condition_state_machine !=  None:
        pre_condition_sm_id = the_state_machine.pre_condition_state_machine.get_id()
    # -- same for trivial pre-conditions        
    trivial_pre_condition_begin_of_line_f = the_state_machine.has_trivial_pre_condition_begin_of_line() 

    # -- raise at each old acceptance state the 'store input position flag'
    # -- set the post conditioned flag for all acceptance states
    for state_idx in orig_acceptance_state_id_list:
        state = result.states[state_idx]
        if not state.has_origin():                       # THIS SHOULD NEVER HAPPEN
            state.add_origin(the_state_machine.get_id(), state_idx, True) 
        state.set_store_input_position_f(True)
        state.set_post_conditioned_acceptance_f(True)
        state.set_pre_condition_id(-1L)   
    
    # -- no acceptance state shall store the input position
    # -- set the post conditioned flag for all acceptance states
    for state_idx in result.get_acceptance_state_list()[0]:
        state = result.states[state_idx]
        if not state.has_origin(): 
            state.add_origin(the_state_machine.get_id(), state_idx, False)
        state.set_store_input_position_f(False)
        state.set_post_conditioned_acceptance_f(True)
        state.set_pre_condition_id(pre_condition_sm_id)   
        state.set_trivial_pre_condition_begin_of_line(trivial_pre_condition_begin_of_line_f)

    return result
