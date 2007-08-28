#! /usr/bin/env python
import sys
from copy import deepcopy
sys.path.append("../")

from core import *


def do(the_state_machine, pre_condition_state_machine):
    """Sets up a pre-condition to the given state machine. This process
       is entirely different from any sequentialization or paralellization
       of state machines. Here, the state machine representing the pre-
       condition ist **not** webbed into the original state machine!

       Instead, the following happens:

          -- the pre-condition state machine is inversed, because
             it is to be walked through backwards.
          -- the inverted state machine is marked with the state machine id
             of the_state_machine.        
          -- the original state machine will refere to the inverse
             state machine of the pre-condition.
          -- the initial state origins and the origins of the acceptance
             states are marked as 'pre-conditioned' indicating the id
             of the inverted state machine of the pre-condition.             
    """
    #___________________________________________________________________________________________
    # (*) do some consistency checking   
    if the_state_machine.__class__.__name__ != "StateMachine":
        raise "expected 1st argument as objects of class StateMachine\n" + \
              "received: " + the_state_machine.__class__.__name__
    if pre_condition_state_machine.__class__.__name__ != "StateMachine":
        raise "expected 2nd argument as objects of class StateMachine\n" + \
              "received: " + pre_condition_state_machine.__class__.__name__

    # -- state machines with no states are senseless here. 
    if the_state_machine.is_empty():
        raise  "empty state machine can have no pre-condition"
    if pre_condition_state_machine.is_empty():
        raise  "empty state machine cannot be a pre-condition"

    # -- trivial pre-conditions should be added last, for simplicity
    if the_state_machine.has_trivial_pre_condition():
        raise "This function was not designed to deal with trivially pre-conditioned state machines." + \
              "Please, make sure the trivial pre-conditioning happens *after* regular pre-conditions."  
    #___________________________________________________________________________________________
        
    # (*) invert the state machine of the pre-condition 
    inverse_pre_condition = pre_condition_state_machine.get_inverse()
    inverse_pre_condition = inverse_pre_condition.get_DFA()
    inverse_pre_condition = inverse_pre_condition.get_hopcroft_optimization()
    # -- mark other state machine with original state machine id
    #    so that code generation known (what did I mean here? fschaef)
    inverse_pre_condition.mark_state_origins(OtherStateMachineID=the_state_machine.get_id())
        
    # (*) let the state machine refer to it
    the_state_machine.pre_condition_state_machine = inverse_pre_condition

    # (*) create origin data, in case where there is none yet create new one.
    #     (do not delete, otherwise existing information gets lost)
    for state_idx in the_state_machine.get_acceptance_state_list()[0]:
        state = the_state_machine.states[state_idx]
        if not state.has_origin(): 
            state.add_origin(the_state_machine.get_id(), state_idx)
        state.set_pre_condition_id(inverse_pre_condition.get_id())
    
    return the_state_machine
