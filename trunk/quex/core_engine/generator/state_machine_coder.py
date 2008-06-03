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

    # -- collect the 'dead end states' (states without further transitions)
    #    create a map from the 'dead end state
    if not BackwardLexingF:
        dead_end_state_db, directly_reached_terminal_id_list = get_dead_end_state_list(state_machine)

    txt = ""
    # -- treat initial state separately 
    if state_machine.is_init_state_a_target_state():
        # (only define the init state label, if it is really needed)
        LabelName = languages_label.get(UserDefinedStateMachineName, 
                                        state_machine.init_state_index, 
                                        {}, None)
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
                                     InitStateF                      = True,
                                     DeadEndStateDB                  = dead_end_state_db)

    # -- all other states
    for state_index, state in state_machine.states.items():
        # the init state has been coded already
        if state_index == state_machine.init_state_index: continue

        state_code = state_transition_coder.do(LanguageDB, UserDefinedStateMachineName, state, state_index,
                                               BackwardLexingF                 = BackwardLexingF,
                                               BackwardInputPositionDetectionF = BackwardInputPositionDetectionF,
                                               DeadEndStateDB                  = dead_end_state_db)

        # some states are not coded (some dead end states)
        if state_code == "": continue

        LabelName = languages_label.get(UserDefinedStateMachineName, state_index, {}, None)
        txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
        txt += "    __QUEX_DEBUG_INFO_ENTER(%s);\n" % __nice(state_index)
        txt += state_code
        txt += "\n"
    
    return txt, directly_reached_terminal_id_list

def get_dead_end_state_list(state_machine):
    """Collect all states that have no further transitions, i.e. dead end states.
       Some of them need to be investigated, since it depends on pre-conditions
       what terminal state is to be considered. The mapping works as follows:

            db.has_key(state_index) == False    ==>  state is not a dead end at all.

            db[state_index] = None              ==> state is a 'gateway' please, jump as usual to 
                                                     the state, the state then routes to the correspondent
                                                     terminal (without input) depending on the 
                                                     pre-conditions.

            db[state_index] = integer           ==> state transits immediately to TERMINAL_n
                                                     where 'n' is the integer.

            db[state_index] = -1                ==> state is a 'harmless' drop out. need to jump to
                                                     general terminal
    """
    db = {}
    directly_reached_terminal_id_list = []
    for state_index, state in state_machine.states.items():
        if not state.transitions().is_empty(): continue

        if state.origins().contains_any_pre_context_dependency():
           # (1) state require run time investigation since pre-conditions have to be checked
           db[state_index] = None
           #     Terminals are reached via a 'router'. nevertheless, they are reached 
           #     without a seek.
           for origin in state.origins().get_list():
               if not origin.is_acceptance(): continue
               directly_reached_terminal_id_list.append(origin.state_machine_id)
        else:
            # find the first acceptance origin (origins are sorted already)
            for origin in state.origins().get_list():
                if origin.is_acceptance():
                    # (2) state transits automatically to terminal given below
                    db[state_index] = origin.state_machine_id
                    directly_reached_terminal_id_list.append(origin.state_machine_id)
                    break
            else:
                # (3) no acceptance origin => terminal general
                db[state_index] = -1  


    return db, directly_reached_terminal_id_list




