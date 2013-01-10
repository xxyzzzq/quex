from   quex.engine.state_machine.core                 import StateMachine, State
from   quex.engine.state_machine.index                import map_state_combination_to_index
import quex.engine.state_machine.algorithm.beautifier as     beautifier

def do(SM_List):
    # Plain merge of all states of all state machines with an 
    # epsilon transition from the init state to all init states
    # of the reverse_sm
    tmp = StateMachine()

    for sm in SM_List:
        tmp.states.update(sm.states)
        tmp.add_epsilon_transition(tmp.init_state_index, sm.init_state_index) 

    result = tmp.clone()

    return beautifier.do(result)

