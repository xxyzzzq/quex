import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
from   quex.core_engine.generator.languages.label import __nice

import quex.core_engine.generator.state_transition_coder as state_transition_coder

def do(state_machine, LanguageDB, 
       UserDefinedStateMachineName="", 
       BackwardLexingF=False, 
       BackwardInputPositionDetectionF=False, 
       EndOfFile_Code=None):
    """Returns the program code implementing the StateMachine's behavior.
       NOTE: This function should only be called on a DFA after the call
             to 'filter_dominated_origins'. The latter is important
             to ensure that for an acceptance state there is only one
             related original state.

       The procedure for each state is the following:
            i)  input <-- next character from stream 
            ii) state transition code (include marking of last success state
                and last success stream position).                  
    """
    assert EndOfFile_Code != None or BackwardLexingF == True

    if BackwardInputPositionDetectionF: assert BackwardLexingF

    txt = ""

    # -- treat initial state separately 
    if state_machine.is_init_state_a_target_state():
        # (only define the init state label, if it is really needed)
        LabelName = languages_label.get(UserDefinedStateMachineName, state_machine.init_state_index)
        txt += "%s\n"  % LanguageDB["$label-definition"](LabelName)

    init_state = state_machine.states[state_machine.init_state_index]
    #
    # NOTE: Only the init state provides a transition via 'EndOfFile'! In any other
    #       case, end of file needs to cause a drop out! After the drop out, lexing
    #       starts at furthest right before the EndOfFile and the init state transits
    #       into the TERMINAL_END_OF_FILE.
    txt += state_transition_coder.do(LanguageDB, 
                                     UserDefinedStateMachineName, 
                                     init_state, 
                                     state_machine.init_state_index,
                                     BackwardLexingF                 = BackwardLexingF,
                                     BackwardInputPositionDetectionF = BackwardInputPositionDetectionF,
                                     CheckEndOfFile_F                = True)

    # -- all other states
    for state_index, state in state_machine.states.items():
        if state_index == state_machine.init_state_index: continue
        LabelName = languages_label.get(UserDefinedStateMachineName, state_index)
        txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
        txt += "    __QUEX_DEBUG_INFO_ENTER(%s);\n" % __nice(state_index)
        txt += state_transition_coder.do(LanguageDB, UserDefinedStateMachineName, state, state_index,
                                         BackwardLexingF                 = BackwardLexingF,
                                         BackwardInputPositionDetectionF = BackwardInputPositionDetectionF)
        txt += "\n"
    
    return txt

