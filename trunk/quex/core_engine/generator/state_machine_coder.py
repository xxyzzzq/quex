import quex.core_engine.generator.languages.core  as languages
from   quex.core_engine.generator.languages.core  import __nice
import quex.core_engine.generator.state_coder as state_coder
import quex.core_engine.state_machine.dead_end_analysis as dead_end_analysis

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

    # -- collect the 'dead end states' (states without further transitions)
    #    create a map from the 'dead end state
    dead_end_state_db, directly_reached_terminal_id_list = dead_end_analysis.do(state_machine)

    if BackwardLexingF:
        # During backward lexing (pre-condition, backward input position detection)
        # there are no dedicated terminal states in the first place.
        directly_reached_terminal_id_list = []

    txt = ""
    # -- treat initial state separately 
    if state_machine.is_init_state_a_target_state():
        # (only define the init state label, if it is really needed)
        txt += LanguageDB["$label-def"]("$entry", state_machine.init_state_index) + "\n"

    init_state = state_machine.states[state_machine.init_state_index]
    #
    # NOTE: Only the init state provides a transition via 'EndOfFile'! In any other
    #       case, end of file needs to cause a drop out! After the drop out, lexing
    #       starts at furthest right before the EndOfFile and the init state transits
    #       into the TERMINAL_END_OF_FILE.
    txt += LanguageDB["$label-def"]("$entry", state_machine.init_state_index) + "\n"
    txt += state_coder.do(LanguageDB, 
                          UserDefinedStateMachineName, 
                          init_state, 
                          state_machine.init_state_index,
                          BackwardLexingF                 = BackwardLexingF,
                          BackwardInputPositionDetectionF = BackwardInputPositionDetectionF,
                          InitStateF                      = True,
                          DeadEndStateDB                  = dead_end_state_db)

    # -- all other states
    for state_index, state in state_machine.states.items():
        # the init state has been coded already
        if state_index == state_machine.init_state_index: continue

        state_code = state_coder.do(LanguageDB, UserDefinedStateMachineName, state, state_index,
                                    BackwardLexingF                 = BackwardLexingF,
                                    BackwardInputPositionDetectionF = BackwardInputPositionDetectionF,
                                    DeadEndStateDB                  = dead_end_state_db)

        # some states are not coded (some dead end states)
        if state_code == "": continue

        txt += LanguageDB["$label-def"]("$entry", state_index) + "\n"
        txt += state_code
        txt += "\n"
    
    return txt, directly_reached_terminal_id_list





