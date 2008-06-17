import quex.core_engine.generator.languages.core   as languages
from   quex.core_engine.generator.languages.core import __nice
import quex.core_engine.generator.transition_block as transition_block
import quex.core_engine.generator.transition       as transition
import quex.core_engine.generator.acceptance_info  as acceptance_info
from   quex.input.setup import setup as Setup
from copy import deepcopy

__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

def do(LanguageDB, StateMachineName, state, StateIdx, BackwardLexingF, 
       BackwardInputPositionDetectionF=False, InitStateF=False,
       DeadEndStateDB={}):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    # (*) check that no epsilon transition triggers to a real state                   
    if __DEBUG_CHECK_ACTIVE_F:
        assert state.transitions().get_epsilon_target_state_index_list() == [], \
               "epsilon transition contained target states: state machine was not made a DFA!\n" + \
               "epsilon target states = " + repr(state.transitions().get_epsilon_target_state_index_list())

    if DeadEndStateDB.has_key(StateIdx):
        return transition.do_dead_end_router(state, StateIdx, StateMachineName, BackwardLexingF, LanguageDB)
       
    TriggerMap = state.transitions().get_trigger_map()
    assert TriggerMap != []  # Only dead end states have empty trigger maps.
    #                        # ==> here, the trigger map cannot be empty.
    #_________________________________________________________________________________________    
    # NOTE: The first entry into the init state is a little different. It does not 
    #       increment the current pointer before referencing the character to be read. 
    #       However, when the init state is entered during analysis else, the current 
    #       pointer needs to be incremented.
    
    txt = ""
    # note down information about success, if state is an acceptance state
    txt += input_block(StateIdx, InitStateF, BackwardLexingF, LanguageDB)

    txt += acceptance_info.do(state, LanguageDB, 
                              BackwardLexingF, BackwardInputPositionDetectionF)

    txt += transition_block.do(state, StateIdx, TriggerMap, LanguageDB, 
                               InitStateF, BackwardLexingF, BackwardInputPositionDetectionF, StateMachineName, 
                               DeadEndStateDB)

    txt += drop_out_handler(state, StateIdx, TriggerMap, 
                            InitStateF, 
                            BackwardLexingF, BackwardInputPositionDetectionF,
                            StateMachineName, LanguageDB, DeadEndStateDB)

    # Define the entry of the init state after the init state itself. This is so,
    # since the init state does not require an increment on the first beat. Later on,
    # when other states enter here, they need to increase/decrease the input pointer.
    if not BackwardLexingF:
        if InitStateF:
            txt += LanguageDB["$label-def"]("$input", StateIdx)
            txt += "    " + LanguageDB["$input/increment"] + "\n"
            txt += "    " + LanguageDB["$goto"]("$entry", StateIdx) + "\n"

    
    return txt # .replace("\n", "\n    ") + "\n"

def input_block(StateIdx, InitStateF, BackwardLexingF, LanguageDB):
    # The initial state starts from the character to be read and is an exception.
    # Any other state starts with an increment (forward) or decrement (backward).
    # This is so, since the beginning of the state is considered to be the 
    # transition action (setting the pointer to the next position to be read).
    txt = ""
    if not BackwardLexingF:
        if not InitStateF:
            txt += LanguageDB["$label-def"]("$input", StateIdx) + "\n"
            txt += "    " + LanguageDB["$input/increment"] + "\n"
    else:
        txt += LanguageDB["$label-def"]("$input", StateIdx) + "\n"
        txt += "    " + LanguageDB["$input/decrement"] + "\n"

    txt += "    " + LanguageDB["$input/get"] + "\n"

    return txt

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

def drop_out_handler(state, StateIdx, TriggerMap, InitStateF, BackwardLexingF, 
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

    if not BackwardLexingF:
        # (*) forward lexical analysis
        if not state.is_acceptance():
            # -- non-acceptance state drop-outs
            goto_str = LanguageDB["$goto-last_acceptance"]

        else:
            # -- acceptance state drop outs
            # -- is the acceptance of the state dependent on pre-conditions?
            #    no  -> directly jump to correspondent terminal
            #    yes -> implement checks for each pre-condition
            if not state.origins().contains_any_pre_context_dependency():
                # 'no' case
                acc_origin = state.origins().find_first_acceptance_origin()
                goto_str   = LanguageDB["$goto"]("$terminal", acc_origin.state_machine_id) 
            else:
                # 'yes' case: acceptance depends on pre-condition flags
                goto_str = acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                                   __goto_distinct_terminal,
                                                                   LanguageDB)

    else:
        # (*) backward lexical analysis
        #     During backward lexing, there are no dedicated terminal states. Only the flags
        #     'pre-condition' fullfilled are set at the acceptance states. On drop out we
        #     transit to the general terminal state (== start of forward lexing).
        goto_str = LanguageDB["$goto"]("$terminal-general", True) 

    txt += "    " + LanguageDB["$if not BLC"]
    txt += "        " + goto_str + "\n" 
    txt += "    " + LanguageDB["$endif"] + "\n"

    # -- in case of the init state, the end of file has to be checked.
    #    (there is no 'begin of file' action in a lexical analyzer when stepping backwards)
    if InitStateF and BackwardLexingF == False:
        txt += "    " + LanguageDB["$if EOF"]
        txt += "        " + LanguageDB["$comment"](
               "NO CHECK 'last_acceptance != -1' --- first state can **never** be an acceptance state") 
        txt += "\n"
        txt += "        " + LanguageDB["$goto"]("$terminal-EOF") + "\n"
        txt += "    " + LanguageDB["$endif"]

    BufferReloadRequiredOnDropOutF = TriggerMap != [] and not BackwardInputPositionDetectionF
    if BufferReloadRequiredOnDropOutF:
        if BackwardLexingF:
            txt += LanguageDB["$drop-out-backward"](StateIdx).replace("\n", "\n    ")
        else:
            txt += LanguageDB["$drop-out-forward"](StateIdx).replace("\n", "\n    ")

    return txt + "\n"
