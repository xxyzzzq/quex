import quex.core_engine.utf8                                          as utf8
import quex.core_engine.regular_expression.snap_backslashed_character as snap_backslashed_character
from quex.core_engine.state_machine.core import StateMachine


def do(sh):
    """Converts a uni-code string into a state machine that parses 
       its letters sequentially. Each state in the sequence correponds
       to the sucessful triggering of a letter. Only the last state, though,
       is an acceptance state. Any bailing out before is 'not accepted'. 
       Example:

       "hey" is translated into the state machine:

           (0)-- 'h' -->(1)-- 'e' -->(2)-- 'y' --> ACCEPTANCE
            |            |            |
           FAIL         FAIL         FAIL
    
      Note: The state indices are globally unique. But, they are not necessarily
            0, 1, 2, ... 
    """
    # resulting state machine
    result = StateMachine()

    # Only \" is a special character '"', any other backslashed character
    # remains as the sequence 'backslash' + character
    while 1 + 1 == 2:
        char_code = utf8.__read_one_utf8_code_from_stream(sh)
        if char_code == ord("\\"): 
            char_code = snap_backslashed_character.do(ucs_letters, i)
            if char_code == None: 
                raise RegularExpressionException("Unidentified backslash-sequence in quoted string.")
               
        new_ucs_letters.append(letter)

    ucs_letters = new_ucs_letters

    state_idx = result.init_state_index
    for letter_code in ucs_letters:
        state_idx = result.add_transition(state_idx, letter_code)

    # when the last state has trigger it is supposed to end up in 'acceptance'
    result.set_acceptance(state_idx)
    return result
