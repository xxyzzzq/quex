#! /usr/bin/env python
import sys
from copy import deepcopy
sys.path.append("../")

from core import *


def do(the_state_machines, LeaveIntermediateAcceptanceStatesF=False):
    """Creates a state machine connecting all state machines in the array 
       'state_machines'. When the flag 'LeaveIntermediateAcceptanceStatesF'
       is given as True, the connection points between the state machines
       will remain  acceptances states. In any other case (e.g. the normal
       sequentialization) the connection points leave there acceptance 
       status and only the last state machine in the list keeps its
       acceptance states.
    """

    if type(the_state_machines) != list or len(the_state_machines) == 0:
        raise "expect argument of type non-empty 'list' received:", repr(the_state_machines)
    if map(lambda x: x.__class__.__name__, the_state_machines) != ["StateMachine"] * len(the_state_machines):
        raise "expected an argument consisting only of objects of State Machines\n" + \
              "received:" + repr(map(lambda x: x.__class__.__name__, the_state_machines))
    # state machines with no states can be deleted from the list. they do not do anything
    # and do not introduce triggers.          
    state_machines = filter(lambda sm: not sm.is_empty(), the_state_machines)         
   
    if len(state_machines) < 2:
        if len(state_machines) < 1: return StateMachine()
        else:                       return state_machines[0]

    # (*) need to clone the state machines, i.e. provide their internal
    #     states with new ids, but the 'behavior' remains. This allows
    #     state machines to appear twice, or being used in 'larger'
    #     conglomerates.
    clone_list = map(lambda sm: sm.clone(), state_machines)

    # (*) collect all transitions from both state machines into a single one
    #     (clone to ensure unique identifiers of states)
    result = clone_list[0]

    # (*) all but last state machine enter the subsequent one, in case of SUCCESS
    #     NOTE: The start index is unique. Therefore, one can assume that each
    #           clone_list '.states' dictionary has different keys. One can simply
    #           take over all transitions of a start index into the result without
    #           considering interferences (see below)
    for next_clone in clone_list[1:]:
        # mount on every success state the initial state of the following state
        # machine via epsilon transition
        result.mount_to_acceptance_states(next_clone.init_state_index, 
                                          CancelStartAcceptanceStateF = not LeaveIntermediateAcceptanceStatesF)
        for start_state_index, states in next_clone.states.items():        
            result.states[start_state_index] = deepcopy(states)
        
    return result
