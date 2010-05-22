import quex.core_engine.state_machine.core                    as state_machine
import quex.core_engine.generator.state_coder.acceptance_info as acceptance_info

from   quex.input.setup import setup as Setup

LanguageDB = None

def do(State, StateIdx, SMD, InitStateF):
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


    if SMD.backward_lexing_f() == False: 
        reload_str           = __reload_forward()
        ## If input == buffer limit code, then the input_p stands on either 
        ## the end of file pointer or the buffer limit. If the end of file
        ## pointer is != 0 it lies before the buffer limit. Thus, in this
        ## case the end of file has been reached.
        load_impossible_str  = "(me->buffer._memory._end_of_file_p != 0x0)"
        ## load_impossible_str  = LanguageDB["$EOF"]
        goto_terminal_str    = __get_forward_goto_terminal_str(State, StateIdx, SMD.sm())
        goto_state_input_str = LanguageDB["$goto"]("$input", StateIdx)
    else:
        reload_str           = __reload_backward()
        load_impossible_str  = LanguageDB["$BOF"]
        goto_terminal_str    = LanguageDB["$goto"]("$terminal-general-bw")
        goto_state_input_str = LanguageDB["$goto"]("$input", StateIdx)

    if len(State.transitions().get_map()) == 0 or SMD.backward_input_position_detection_f():
        reload_str = ""

    if InitStateF and SMD.backward_lexing_f() == False:
        # Initial State in forward lexing is special! See comments above!
        txt = [ 
            LanguageDB["$label-def"]("$drop-out", StateIdx),
            "    ", LanguageDB["$if"], LanguageDB["$not BLC"],  LanguageDB["$then"], 
            LanguageDB["$label-def"]("$drop-out-direct", StateIdx), 
            "        ", LanguageDB["$goto"]("$terminal-FAILURE"),                   "\n",
            "    ", LanguageDB["$elseif"], load_impossible_str, LanguageDB["$then"], 
            "        ", LanguageDB["$goto"]("$terminal-EOF"),                       "\n",
            "    ", LanguageDB["$endif"],                                           "\n",
            "    ", reload_str,
            "    ", goto_state_input_str,                                           "\n",
        ]

    else:
        # Normal Drop-Out. See comments above!
        txt = [ 
            LanguageDB["$label-def"]("$drop-out", StateIdx),
            "    ", LanguageDB["$if"], "   ", LanguageDB["$not BLC"], "\n",
            "    ", " " * len(LanguageDB["$if"]), LanguageDB["$or"], 
                    " ", load_impossible_str, " ", 
                    LanguageDB["$then"],                            
            LanguageDB["$label-def"]("$drop-out-direct", StateIdx), 
            "        ", goto_terminal_str,                            "\n",
            "    ",     LanguageDB["$endif"],                         "\n",
            "    ", reload_str,                                       "\n",
            "    ", goto_state_input_str,                             "\n",
        ]

    # -- in case of the init state, the end of file has to be checked.
    return txt

def __reload_forward():
    # NOTE, extra four whitespace in second line by purpose.
    return "QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,\n" \
           "                                       post_context_start_position, PostContextStartPositionN);"

def __reload_backward(): 
    return "QUEX_NAME(buffer_reload_backward)(&me->buffer);\n"

def __get_forward_goto_terminal_str(state, StateIdx, SM):
    assert isinstance(state, state_machine.State)
    assert isinstance(SM, state_machine.StateMachine)
    global LanguageDB 

    # (1) non-acceptance state drop-outs
    #     (winner is determined by variable 'last_acceptance', then goto terminal router)
    if not state.is_acceptance() \
       or  state.__class__.__name__ == "TemplateState": 
        return LanguageDB["$goto-last_acceptance"]

    def __goto_terminal(Origin):
        assert Origin.is_acceptance()
        global LanguageDB 
        return LanguageDB["$goto"]("$terminal-direct", Origin.state_machine_id)

    # -- acceptance state drop outs
    return acceptance_info.get_acceptance_detector(state.origins().get_list(), __goto_terminal)



