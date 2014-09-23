# (C) Frank-Rene Schaefer
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.algorithm.beautifier  as beautifier
from   quex.blackboard                                 import setup as Setup

from   quex.engine.tools import typed, \
                                flatten_list_of_lists

@typed(X=(StateMachine,None))
def do_state_machine(X):
    """Transforms a given state machine from 'Unicode Driven' to another
       character encoding type.
    
       RETURNS: 
       [0] Transformation complete (True->yes, False->not all transformed)
       [1] Transformed state machine. It may be the same as it was 
           before if there was no transformation actually.

       It is ensured that the result of this function is a DFA compliant
       state machine.
    """
    if X is None: return True, None
    assert X.is_DFA_compliant()

    complete_f, sm = Setup.buffer_codec.transform(X)

    if sm.is_DFA_compliant(): return complete_f, sm
    else:                     return complete_f, beautifier.do(sm)

def do_set(number_set, TrafoInfo, fh=-1):
    """RETURNS: True  transformation successful
                False transformation failed, number set possibly in inconsistent state!
    """
    return TrafoInfo.transform_NumberSet(number_set)

def do_character(Character, TrafoInfo, fh=-1):
    """The current implementation is, admitably, not very fast. 
    Improve upon detection of speed issues.

    RETURNS: A list of integers which represent the character in the 
             given TrafoInfo.
    """
    return TrafoInfo.transform_Number(Character) 

def do_sequence(Sequence, TrafoInfo=None, fh=-1):
    if TrafoInfo is None:
        TrafoInfo = Setup.buffer_codec

    return flatten_list_of_lists(
        do_character(x, TrafoInfo, fh)
        for x in Sequence
    )



