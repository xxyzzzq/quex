from   quex.input.setup import setup as Setup
import quex.core_engine.generator.acceptance_info  as acceptance_info

def do(state, StateIdx, TriggerMap, InitStateF, BackwardLexingF, 
       BackwardInputPositionDetectionF, StateMachineName, LanguageDB, 
       DeadEndStateDB):
    """There are two reasons for drop out:
       
          (1) A buffer limit code has been reached.

          (2) The current character does not fit in the trigger map (regular drop out).
       
       Case (1) differs from case (2) in the fact that input == buffer limit code. 
       If a buffer limit code is reached, a buffer reload needs to be initiated. If
       the character drops over the edge, then a terminal state needs to be targeted.
    """
    # -- drop out code (transition to no target state)
    txt = LanguageDB["$label-def"]("$drop-out", StateIdx)
    txt += "    " + LanguageDB["$if not BLC"]
    txt += "        " + get_drop_out_goto_string(state, BackwardLexingF) + "\n" 
    txt += "    " + LanguageDB["$endif"] + "\n"

    # -- in case of the init state, the end of file has to be checked.
    #    (there is no 'begin of file' action in a lexical analyzer when stepping backwards)
    if InitStateF and BackwardLexingF == False:
        txt += "    " + LanguageDB["$if EOF"]
        comment = "NO CHECK 'last_acceptance != -1' --- first state can **never** be an acceptance state" 
        txt += "        " + LanguageDB["$comment"](comment) + "\n"
        txt += "        " + LanguageDB["$goto"]("$terminal-EOF") + "\n"
        txt += "    " + LanguageDB["$endif"]

    BufferReloadRequiredOnDropOutF = TriggerMap != [] and not BackwardInputPositionDetectionF
    if BufferReloadRequiredOnDropOutF:
        if BackwardLexingF:
            txt += LanguageDB["$drop-out-backward"](StateIdx).replace("\n", "\n    ")
        else:
            txt += LanguageDB["$drop-out-forward"](StateIdx).replace("\n", "\n    ")

    return txt + "\n"

def __goto_distinct_terminal(Origin):
    """Special for the drop out case"""
    LanguageDB = Setup.language_db
    txt = ""
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        txt += LanguageDB["$input/seek_position"]("last_acceptance_input_position")
    txt += LanguageDB["$goto"]("$terminal", Origin.state_machine_id)
    return txt

def get_drop_out_goto_string(state, BackwardLexingF):
    LanguageDB = Setup.language_db

    if not BackwardLexingF:
        # (*) forward lexical analysis
        if not state.is_acceptance():
            # -- non-acceptance state drop-outs
            return LanguageDB["$goto-last_acceptance"]

        else:
            # -- acceptance state drop outs
            # -- is the acceptance of the state dependent on pre-conditions?
            #    no  -> directly jump to correspondent terminal
            #    yes -> implement checks for each pre-condition
            if not state.origins().contains_any_pre_context_dependency():
                # 'no' case
                acc_origin = state.origins().find_first_acceptance_origin()
                return LanguageDB["$goto"]("$terminal", acc_origin.state_machine_id) 
            else:
                # 'yes' case: acceptance depends on pre-condition flags
                return acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                               __goto_distinct_terminal,
                                                               LanguageDB)

    else:
        # (*) backward lexical analysis
        #     During backward lexing, there are no dedicated terminal states. Only the flags
        #     'pre-condition' fullfilled are set at the acceptance states. On drop out we
        #     transit to the general terminal state (== start of forward lexing).
        return LanguageDB["$goto"]("$terminal-general", True) 

