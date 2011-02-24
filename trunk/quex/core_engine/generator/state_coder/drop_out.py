import quex.core_engine.state_machine.core                    as state_machine
import quex.core_engine.generator.state_coder.acceptance_info as acceptance_info
from   quex.core_engine.generator.languages.core              import get_address

from   quex.input.setup            import setup as Setup
from   quex.frs_py.string_handling import blue_print

LanguageDB = None

normal_drop_out_template = """
$$LABEL_DIRECT$$
$$GOTO_TERMINAL$$
"""

normal_reload_template = """
$$LABEL$$
    QUEX_GOTO_RELOAD($$DIRECTION$$, $$STATE_INDEX$$, $$TERMINAL$$);
"""

init_drop_out_template = """
$$LABEL_DIRECT$$
$$GOTO_FAILURE$$
"""

init_reload_template = """
$$LABEL$$
    goto __RELOAD_INIT_STATE;
"""

def do(State, StateIdx, SMD):
    """There are two reasons for drop out:
       
          (1) A buffer limit code has been reached.

          (2) The current character does not fit in the trigger map (regular drop out).
       
       Case (1) differs from case (2) in the fact that input == buffer limit code. 
       If a buffer limit code is reached, a buffer reload needs to be initiated. If
       the character drops over the edge, then a terminal state needs to be targeted.
       
                                      no
         'input' == BufferLimitCode? ------------------.         
                    |                                  |
                    | yes                              |
                    "                 yes              "
                end of file?   -------------->  goto terminal of 
                    |                            winning pattern
                    | no
                    "
            -- reload content
            -- retry current state
               with fresh 'input'.


       Note, that no error handling for 'reload content' is necessary, since
       no acceptable reason (such as EOF) for failure remains. On End of file
       we transit to the winning terminal and leave the detection of 'End of FILE'
       to the init state. (This spares an EOF check at the end of every terminal.)

       The following C-Code statement does the magic briefly and clearly:
         
             if( input != BLC || buffer at EOF? ) {
                 goto winning terminal;
             }
             reload();
             goto input;

       NOTE: The initial state is a little different, it needs to detect the EOF
             and jump to the EOF terminal if so, thus:

                                      no
         'input' == BufferLimitCode? -------->  goto FAILURE terminal 
                    |                            
                    | yes                               
                    "                 yes               
                end of file?   -------------->  goto EOF terminal
                    |                           
                    | no
                    "
            -- reload content
            -- retry current state
               with fresh 'input'.

       NOTE: There cannot be a 'winning' pattern on a drop-out of the initial state, 
             because otherwise, this would mean: nothing is acceptable, and thus
             the analyzis was stuck on the init state.

       The correspondent C-code is straight forward:

            if( input != BLC )       goto FAILURE;
            else if( buffer at EOF ) goto END_OF_FILE;
            reload();
            goto input;

       NOTE: In backward analyzsis a FAILURE simply means that no pre-condition 
             is fulfilled and there is no special action about it. Also, 
             there is no special action on 'BEGIN_OF_FILE'. Thus when backward
             lexing, there is no special treatment of the initial state.
    """
    global LanguageDB 
    assert SMD.__class__.__name__ == "StateMachineDecorator"
    LanguageDB = Setup.language_db
    InitStateF = (StateIdx == SMD.sm().init_state_index)

    if InitStateF and SMD.forward_lexing_f():
        # Initial State in forward lexing is special! See comments above!
        txt = blue_print(init_drop_out_template,
                         [
                          ["$$LABEL_DIRECT$$",       LanguageDB["$label-def"]("$drop-out-direct", StateIdx)],
                          ["$$GOTO_FAILURE$$",       "    " + LanguageDB["$goto"]("$terminal-FAILURE")],
                         ])

    else:
        if SMD.forward_lexing_f(): 
            goto_terminal_str = __get_forward_goto_terminal_str(State, StateIdx, SMD.sm())
        else:
            goto_terminal_str = "    " + LanguageDB["$goto"]("$terminal-general-bw")

        txt = blue_print(normal_drop_out_template,
                         [
                          ["$$LABEL_DIRECT$$",    LanguageDB["$label-def"]("$drop-out-direct", StateIdx)],
                          ["$$GOTO_TERMINAL$$",   goto_terminal_str], 
                         ])

    # txt += LanguageDB["$label-def"]("$reload", StateIdx) + "\n"
    # txt += get_transition_to_reload(StateIdx, SMD, StateIndexStr)

    # -- in case of the init state, the end of file has to be checked.
    return [ txt ]

def __goto_terminal(Origin):
    global LanguageDB 
    # Case if no un-conditional acceptance, the goto general terminal
    if type(Origin) == type(None): return LanguageDB["$goto-last_acceptance"]
    assert Origin.is_acceptance()
    return "    " + LanguageDB["$goto"]("$terminal-direct", Origin.state_machine_id)

def __get_forward_goto_terminal_str(state, StateIdx, SM):
    assert isinstance(state, state_machine.State)
    assert isinstance(SM, state_machine.StateMachine)
    global LanguageDB 

    # (1) non-acceptance state drop-outs
    #     (winner is determined by variable 'last_acceptance', then goto terminal router)
    if state.__class__.__name__ == "TemplateState": 
        return "    goto __TERMINAL_ROUTER;"

    elif not state.is_acceptance():
        return "    goto __TERMINAL_ROUTER;"

    else:
        # -- acceptance state drop outs
        return acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                       __goto_terminal)



