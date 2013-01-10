"""Algebraic relations:

    inverse(\Any*} == \None
    \Not{\None}    == \Any*

    inverse(intersection(A, B)) == union(inverse(A), inverse(B))
    inverse(union(A, B))        == intersection(inverse(A), inverse(B))
"""
import quex.engine.state_machine.index as     index
from   quex.engine.state_machine.core  import State

def do(SM):
    """RETURN: A state machines that matches anything which is 
               not matched by SM.

       Idea: The paths along SM do not guide to acceptance states,
             but to normal states.

             Any drop-out is translated into a transition into 
             the 'accept all state'.

       NOTE: This function produces a finite state automaton which
             is not applicable by itself. It would eat ANYTHING
             from a certain state on.
    """
    result = SM.clone()
    for state in result.get_acceptance_state_list():
        state.set_acceptance(False)

    accept_all_state_index = index.get()
    result.states[accept_all_state_index] = State(AcceptanceF=True, 
                                                  StateIndex=accept_all_state_index)

    for state in result.states.itervalues():
        trigger_set = state.transitions().get_trigger_set_union()
        inverse_trigger_set = trigger_set.inverse()
        state.add_transition(inverse_trigger_set, accept_all_state_index)

    return result

