import quex.core_engine.utf8                                          as utf8
import quex.core_engine.regular_expression.snap_backslashed_character as snap_backslashed_character
from quex.core_engine.state_machine.core import StateMachine


def do(UTF8_String):
    """Converts a uni-code string into a state machine that parses 
       its letters sequentially. Each state in the sequence correponds
       to the sucessful triggering of a letter. Only the last state, though,
       is an acceptance state. Any bailing out before is 'not accepted'. 
       Example:

       "hey" is translated into the state machine:

           (0)-- 'h' -->(1)-- 'e' -->(2)-- 'y' --> SUCCESS
            |            |            |
           FAIL         FAIL         FAIL
    
      Note: The state indices are globally unique. But, they are not necessarily
            0, 1, 2, ... 
    """
    # resulting state machine
    result = StateMachine()

    # -- interpret the given 'normal' string as utf8 encoded
    # -- translate the string into 'int' numbers representing the 
    #    ucs code of each letter.
    ucs_letters = utf8.map_n_utf8_to_unicode(UTF8_String)

    # Only \" is a special character '"', any other backslashed character
    # remains as the sequence 'backslash' + character
    new_ucs_letters = []
    i = -1
    while i < len(ucs_letters) - 1:
        i += 1
        letter = ucs_letters[i]
        if letter == ord("\\") and i < len(ucs_letters) - 1: 
            char_code, i = snap_backslashed_character.do(ucs_letters, i)
            if char_code != None: 
                letter = char_code
                i -= 1
               
        new_ucs_letters.append(letter)

    ucs_letters = new_ucs_letters

    state_idx = result.init_state_index
    for letter_code in ucs_letters:
        state_idx = result.add_transition(state_idx, letter_code)

    # when the last state has trigger it is supposed to end up in 'acceptance'
    result.set_acceptance(state_idx)
    return result
