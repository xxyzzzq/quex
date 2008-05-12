import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
import quex.core_engine.generator.transition_block as transition_block
from copy import deepcopy
__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

def do(LanguageDB, StateMachineName, state, StateIdx, BackwardLexingF, 
       BackwardInputPositionDetectionF=False, InitStateF=False):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    # (*) check that no epsilon transition triggers to a real state                   
    if __DEBUG_CHECK_ACTIVE_F:
        assert state.transitions().get_epsilon_target_state_index_list() == [], \
               "epsilon transition contained target states: state machine was not made a DFA!\n" + \
               "epsilon target states = " + repr(state.transitions().get_epsilon_target_state_index_list())
       
    TriggerMap = state.transitions().get_trigger_map()
    #_________________________________________________________________________________________    
    
    txt = ""
    # note down information about success, if state is an acceptance state
    txt += acceptance_info(state, LanguageDB, 
                           BackwardLexingF, BackwardInputPositionDetectionF)

    txt += input_block(StateIdx, TriggerMap == [], InitStateF, BackwardLexingF, LanguageDB)

    txt += transition_block.do(state, StateIdx, TriggerMap, LanguageDB, 
                               InitStateF, BackwardLexingF, StateMachineName)

    txt += drop_out_block(state, StateIdx, TriggerMap, 
                          InitStateF, BackwardLexingF, StateMachineName, LanguageDB)
    
    return txt.replace("\n", "\n    ") + "\n"


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
    txt = LanguageDB["$label-definition"](input_label) + "\n"

    if not BackwardLexingF:
        txt += "%s\n" % LanguageDB["$input/get"] 
    else:
        # At the init state, the lexial analyzer stands **before** the next character
        # to be read in forward direction. When backward lexing is involved the input
        # position needs to be put one ahead.
        #                               LE
        #                                *
        #         | | | | | | |p|r|i|n|t|f|(| | | | | | | | | | | | |
        #                                  *
        #                                  NC
        # current_p = LE (lexeme end), so that "input = *(++current_p)" is '('.
        # NOW: current_p = NC, so that         "input = *(--current_p)" is 'f'.
        if InitStateF: txt += LanguageDB["$input/get"]
        txt += "%s\n" % LanguageDB["$input/get-backwards"]   
    txt += "    " + LanguageDB["$debug-info-input"] + "\n"

    return txt

def drop_out_block(state, StateIdx, TriggerMap, InitStateF, BackwardLexingF, StateMachineName, LanguageDB):
    # -- drop out code (transition to no target state)
    drop_out_label = languages_label.get_drop_out(StateIdx)
    txt  = LanguageDB["$label-definition"](drop_out_label) + "\n"

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
        txt += LanguageDB["$if EOF"]
        txt += "    " + LanguageDB["$comment"](
                "NO CHECK 'last_acceptance != -1' --- first state can **never** be an acceptance state") 
        txt += "\n"
        txt += "    " + LanguageDB["$transition"](StateMachineName, StateIdx, "END_OF_FILE", 
                                                  BackwardLexingF=False) + "\n"
        txt += LanguageDB["$endif"]

    txt += LanguageDB["$drop-out"](StateMachineName, StateIdx, BackwardLexingF,
                                   BufferReloadRequiredOnDropOutF = TriggerMap != [],
                                   CurrentStateIsAcceptanceF      = state.is_acceptance(),
                                   OriginList                     = state.origins().get_list(),
                                   LanguageDB                     = LanguageDB,
                                   DropOutTargetStateID           = drop_out_target_state_id)
        

    return txt + "\n"

