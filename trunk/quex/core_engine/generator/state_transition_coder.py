import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.transition_block as transition_block
import quex.core_engine.generator.acceptance_info as acceptance_info
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
        return transition.do_dead_end_router(state, StateIdx, DeadEndStateDB[StateIdx], 
                                             StateMachineName, LanguageDB)
       
    TriggerMap = state.transitions().get_trigger_map()
    assert TriggerMap != []  # Only dead end states have empty trigger maps.
    #                        # ==> here, the trigger map cannot be empty.
    #_________________________________________________________________________________________    
    
    txt = ""
    # note down information about success, if state is an acceptance state
    txt += acceptance_info.do(state, LanguageDB, 
                              BackwardLexingF, BackwardInputPositionDetectionF)

    txt += input_block(StateIdx, InitStateF, BackwardLexingF, LanguageDB)

    txt += transition_block.do(state, StateIdx, TriggerMap, LanguageDB, 
                               InitStateF, BackwardLexingF, StateMachineName, 
                               DeadEndStateDB)

    txt += drop_out_handler(state, StateIdx, TriggerMap, 
                            InitStateF, 
                            BackwardLexingF, BackwardInputPositionDetectionF,
                            StateMachineName, LanguageDB, DeadEndStateDB)
    
    return txt # .replace("\n", "\n    ") + "\n"


def input_block(StateIdx, InitStateF, BackwardLexingF, LanguageDB):

    txt = LanguageDB["$label-def"]["$input"](StateIdx) + "\n"

    # The initial state starts from the character to be read and is an exception.
    # Any other state starts with an increment (forward) or decrement (backward).
    # This is so, since the beginning of the state is considered to be the 
    # transition action (setting the pointer to the next position to be read).
    if not InitStateF:
        if BackwardLexingF: txt += "    " + LanguageDB["$intput/decrement"] + "\n"
        else:               txt += "    " + LanguageDB["$intput/increment"] + "\n"
    txt += "    " + LanguageDB["$input/get"] + "\n"

    return txt

def drop_out_handler(state, StateIdx, TriggerMap, InitStateF, BackwardLexingF, 
                     BackwardInputPositionDetectionF, StateMachineName, LanguageDB, DeadEndStateDB):
    # -- drop out code (transition to no target state)
    txt = LanguageDB["$label-def"]["$drop-out"](StateIdx) + "\n"

    drop_out_target_state_id = -1L
    if len(TriggerMap) == 1:
        # We cannot transit to any subsequent state without checking wether
        # the received character was a buffer limit code. To prevent an 
        # unconditional goto, rewrite the drop out in such a way that by
        # default it moves to the given target state. In case of buffer limit
        # code it returns in order to read the next character.
        drop_out_target_state_id = TriggerMap[0][1]

    # -- in case of the init state, the end of file has to be checked.
    #    (there is no 'begin of file' action in a lexical analyzer when stepping backwards)
    if InitStateF and BackwardLexingF == False:
        txt += "    " + LanguageDB["$if EOF"]
        txt += "        " + LanguageDB["$comment"](
               "NO CHECK 'last_acceptance != -1' --- first state can **never** be an acceptance state") 
        txt += "\n"
        txt += "        " + LanguageDB["$goto"]["$terminal-EOF"]
        txt += "    " + LanguageDB["$endif"]

    BRRODO_f = TriggerMap != [] and not BackwardInputPositionDetectionF
    txt += LanguageDB["$drop-out"](StateMachineName, StateIdx, BackwardLexingF,
                                   BufferReloadRequiredOnDropOutF = BRRODO_f,
                                   CurrentStateIsAcceptanceF      = state.is_acceptance(),
                                   OriginList                     = state.origins().get_list(),
                                   LanguageDB                     = LanguageDB,
                                   DropOutTargetStateID           = drop_out_target_state_id)

    return txt + "\n"






