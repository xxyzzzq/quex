from   quex.engine.state_machine.core                 import StateMachine, State
from   quex.engine.state_machine.index                import map_state_combination_to_index
import quex.engine.state_machine.parallelize          as     parallelize
import quex.engine.state_machine.algorithm.beautifier as     beautifier

def do(SM_List):
    """The 'parallelize' module does a union of multiple state machines,
    even if they have different origins and need to be combined carefully.
    There is no reason, why another 'union' operation should be implemented
    in this case.
    """
    result = parallelize.do(SM_List)
    return beautifier.do(result)

