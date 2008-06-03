import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
import quex.core_engine.generator.transition_block as transition_block
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
    txt += acceptance_info(state, LanguageDB, 
                           BackwardLexingF, BackwardInputPositionDetectionF)

    txt += input_block(StateIdx, TriggerMap == [], InitStateF, BackwardLexingF, LanguageDB)

    txt += transition_block.do(state, StateIdx, TriggerMap, LanguageDB, 
                               InitStateF, BackwardLexingF, StateMachineName, 
                               DeadEndStateDB)

    txt += transition.do_drop_out_router(state, StateIdx, TriggerMap, 
                                         InitStateF, 
                                         BackwardLexingF, BackwardInputPositionDetectionF,
                                         StateMachineName, LanguageDB, DeadEndStateDB)
    
    return txt # .replace("\n", "\n    ") + "\n"

def acceptance_info(state, LanguageDB, 
                    BackwardLexingF, 
                    BackwardInputPositionDetectionF=False):
    """Two cases:
       -- an origin marks an acceptance state without any post-condition:
          store input position and mark last acceptance state as the state machine of 
          the origin (note: this origin may result through a priorization)
       -- an origin marks an acceptance of an expression that has a post-condition.
          store the input position in a dedicated input position holder for the 
          origins state machine.
    """
    if BackwardInputPositionDetectionF: assert BackwardLexingF

    OriginList = state.origins().get_list()

    if BackwardLexingF:
        # (*) Backward Lexing 
        if not BackwardInputPositionDetectionF:
            return LanguageDB["$acceptance-info-bw"](OriginList, LanguageDB)
        else:
            return LanguageDB["$acceptance-info-bwfc"](OriginList, LanguageDB)
    else:
        # (*) Forward Lexing 
        return LanguageDB["$acceptance-info-fw"](OriginList, LanguageDB)

def input_block(StateIdx, TriggerMapEmptyF, InitStateF, BackwardLexingF, LanguageDB):

    if TriggerMapEmptyF: return ""

    input_label = languages_label.get_input(StateIdx)
    txt         = LanguageDB["$label-definition"](input_label) + "\n"

    # The initial state starts from the character to be read and is an exception.
    # Any other state starts with an increment (forward) or decrement (backward).
    # This is so, since the beginning of the state is considered to be the 
    # transition action (setting the pointer to the next position to be read).
    if not InitStateF:
        if BackwardLexingF: txt += "    " + LanguageDB["$intput/decrement"] + "\n"
        else:               txt += "    " + LanguageDB["$intput/increment"] + "\n"
    txt += "    " + LanguageDB["$intput/get"] + "\n"

    return txt






