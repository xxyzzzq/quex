from   quex.input.setup import setup as Setup
import quex.core_engine.generator.acceptance_info  as acceptance_info
LanguageDB = Setup.language_db

def do(state, StateIdx, SM, InitStateF):
    """There are two reasons for drop out:
       
          (1) A buffer limit code has been reached.

          (2) The current character does not fit in the trigger map (regular drop out).
       
       Case (1) differs from case (2) in the fact that input == buffer limit code. 
       If a buffer limit code is reached, a buffer reload needs to be initiated. If
       the character drops over the edge, then a terminal state needs to be targeted.
    """
    assert SM.__class__.__name__ == "StateMachineDecorator"

    TriggerMap = state.transitions().get_trigger_map()

    # -- drop out code (transition to no target state)
    txt = LanguageDB["$label-def"]("$drop-out", StateIdx)
    txt += "    " + LanguageDB["$if not BLC"]
    # -- if it's clear that it's not a buffer limit code, then jump directly
    txt += LanguageDB["$label-def"]("$drop-out-direct", StateIdx)
    txt += "        " + get_drop_out_goto_string(state, StateIdx, SM.sm(), SM.backward_lexing_f()) + "\n" 
    txt += "    " + LanguageDB["$endif"] + "\n"

    # -- in case of the init state, the end of file has to be checked.
    #    (there is no 'begin of file' action in a lexical analyzer when stepping backwards)
    if InitStateF and SM.backward_lexing_f() == False:
        txt += "    " + LanguageDB["$if EOF"]
        comment = "NO CHECK 'last_acceptance != -1' --- first state can **never** be an acceptance state" 
        txt += "        " + LanguageDB["$comment"](comment) + "\n"
        txt += "        " + LanguageDB["$goto"]("$terminal-EOF") + "\n"
        txt += "    " + LanguageDB["$endif"]

    BufferReloadRequiredOnDropOutF = TriggerMap != [] and not SM.backward_input_position_detection_f()
    if BufferReloadRequiredOnDropOutF:
        if SM.backward_lexing_f():
            txt += "    " + __reload_backward(StateIdx, SM)
        else:
            # In case that it cannot load anything, it still needs to know where to jump to.
            txt += "    " + acceptance_info.forward_lexing(state, StateIdx, SM.sm(), ForceF=True)
            txt += "    " + __reload_forward(StateIdx, SM)

    return txt + "\n"

def __reload_forward(StateIndex, SM): 
    arg_list = ""
    for state_machine_id in SM.post_contexted_sm_id_list():
        arg_list += ", &last_acceptance_%s_input_position" % state_machine_id
    txt  = 'QUEX_DEBUG_PRINT(&me->buffer, "FORWARD_BUFFER_RELOAD");\n'
    txt += "if( $$QUEX_ANALYZER_STRUCT_NAME$$_%s_buffer_reload_forward(me->buffer_filler, &last_acceptance_input_position%s) ) {\n" % \
            (SM.name(), arg_list)
    txt += "   " + LanguageDB["$goto"]("$input", StateIndex) + "\n"
    txt += LanguageDB["$endif"]                              + "\n"
    txt += 'QUEX_DEBUG_PRINT(&me->buffer, "BUFFER_RELOAD_FAILED");\n'
    txt += LanguageDB["$goto-last_acceptance"]               + "\n"
    return txt

def __reload_backward(StateIndex, SM): 
    txt  = 'QUEX_DEBUG_PRINT(&me->buffer, "BACKWARD_BUFFER_RELOAD");\n'
    txt += "if( QuexAnalyser_buffer_reload_backward(me->buffer_filler) ) {\n"
    txt += "   " + LanguageDB["$goto"]("$input", StateIndex) + "\n"
    txt += LanguageDB["$endif"]                              + "\n"
    txt += 'QUEX_DEBUG_PRINT(&me->buffer, "BUFFER_RELOAD_FAILED");\n'
    txt += LanguageDB["$goto"]("$terminal-general")          + "\n"
    return txt

def __goto_distinct_terminal(Origin):
    LanguageDB = Setup.language_db
    return LanguageDB["$goto"]("$terminal", Origin.state_machine_id)

def __goto_distinct_terminal_direct(Origin):
    LanguageDB = Setup.language_db
    return LanguageDB["$goto"]("$terminal-direct", Origin.state_machine_id)

def get_drop_out_goto_string(state, StateIdx, SM, BackwardLexingF):
    assert state.__class__.__name__ == "State"
    assert SM.__class__.__name__ == "StateMachine"
    LanguageDB = Setup.language_db

    if not BackwardLexingF:
        # (*) forward lexical analysis
        if not state.is_acceptance():
            # -- non-acceptance state drop-outs
            return LanguageDB["$goto-last_acceptance"]

        else:
            if acceptance_info.do_subsequent_states_require_storage_of_last_acceptance_position(StateIdx, state, SM):
                callback = __goto_distinct_terminal
            else:
                callback = __goto_distinct_terminal_direct
            # -- acceptance state drop outs
            return acceptance_info.get_acceptance_detector(state.origins().get_list(), callback)

    else:
        # (*) backward lexical analysis
        #     During backward lexing, there are no dedicated terminal states. Only the flags
        #     'pre-condition' fullfilled are set at the acceptance states. On drop out we
        #     transit to the general terminal state (== start of forward lexing).
        return LanguageDB["$goto"]("$terminal-general", True) 

