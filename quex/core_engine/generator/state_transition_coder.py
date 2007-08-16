import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
from copy import deepcopy


def do(Language, StateMachineName, state, StateIdx, BackwardLexingF):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    # (*) check that no epsilon transition triggers to a real state                   
    if state.get_epsilon_target_state_indices() != []:
        raise "epsilon transition contained target states: state machine was not made a DFA!\n" + \
              "epsilon target states = " + repr(state.get_epsilon_target_state_indices())
       
    #_________________________________________________________________________________________    
    TriggerMap = state.get_trigger_map()
    LanguageDB = languages.db[Language]
    
    # note down information about success, if state is an acceptance state
    code_str = "    "   
    code_str += LanguageDB["$acceptance-info"](state.get_origin_list(), LanguageDB, BackwardLexingF)
    
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       i.e states with no transition trigger map. If those can be avoided, then
    #       this variable can be replaced by 'True'
    if TriggerMap != []:
        empty_trigger_map_f = False

        input_label = languages_label.get_input(StateMachineName, StateIdx)
        code_str += LanguageDB["$label-definition"](input_label) + "\n"
        #
        if not BackwardLexingF: code_str += "%s\n" % LanguageDB["$input/get"] 
        else:                   code_str += "%s\n" % LanguageDB["$input/get-backwards"] 

        txt = __get_code(state,TriggerMap, LanguageDB, 
                         StateMachineName, StateIdx, 
                         BackwardLexingF = BackwardLexingF)

    else:
        empty_trigger_map_f = True
        # Empty State (no transitions, but the epsilon transition)
        txt = "$/* no trigger set $*/"

        # trigger outside the trigger intervals
        txt += "\n" + LanguageDB["$transition"](StateMachineName, StateIdx,
                                                state.is_acceptance(),
                                                None,
                                                state.get_origin_list(),
                                                BackwardLexingF                = BackwardLexingF, 
                                                BufferReloadRequiredOnDropOutF = False)

        txt = txt.replace("\n", "\n    ")

    code_str += txt + "\n"

    # -- drop out code (transition to no target state)
    drop_out_label = languages_label.get_drop_out(StateMachineName, StateIdx)
    txt  = LanguageDB["$label-definition"](drop_out_label) + "\n"
    txt += LanguageDB["$drop-out"](StateMachineName, StateIdx, BackwardLexingF,
                                   BufferReloadRequiredOnDropOutF = not empty_trigger_map_f,
                                   CurrentStateIsAcceptanceF      = state.is_acceptance(),
                                   OriginList                     = state.get_origin_list())
        
    txt = txt.replace("\n", "\n    ")
    code_str += txt + "\n"

    return languages.replace_keywords(code_str, LanguageDB, NoIndentF=True)


def __get_code(state, TriggerMap, LanguageDB, StateMachineName, StateIdx, BackwardLexingF):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    TriggerSetN = len(TriggerMap)

    # (*) check that the trigger map consist of sorted adjacent intervals 
    #     This assumption is critical because it is assumed that for any
    #     isolated interval the bordering intervals have bracketed the remaining
    #     cases!
    if TriggerSetN > 1:
        previous_interval = TriggerMap[0][0] 
        for trigger_interval, target_state_index in TriggerMap[1:]:
            if trigger_interval.begin != previous_interval.end:
                raise "non-adjacent intervals in TriggerMap\n" + \
                      "TriggerMap = " + repr(TriggerMap)
            if trigger_interval.end <= previous_interval.begin:
                raise "unsorted intervals in TriggerMap\n" + \
                      "TriggerMap = " + repr(TriggerMap)
            previous_interval = deepcopy(trigger_interval)

        
    #________________________________________________________________________________
    txt = "    "

    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        #     
        #     -- target state != None, then the machine is still eating
        #                                   => transition to subsequent state.
        #
        #     -- target state == None, drop into a terminal state.
        #
        #     for details about $transition, see the __transition() function of the
        #     respective language module.
        #
        target_state_index = TriggerMap[0][1]       
        #
        txt += "%s" % LanguageDB["$transition"](StateMachineName, 
                                                StateIdx,
                                                state.is_acceptance(),
                                                target_state_index,
                                                state.get_origin_list(),
                                                BackwardLexingF) 
        txt += "    $/* %s $*/" % TriggerMap[0][0].get_utf8_string()
        
    else:    
        # two or more intervals => cut in the middle
        MiddleTrigger_Idx = int(TriggerSetN / 2)
        middle = TriggerMap[MiddleTrigger_Idx]

        if middle[0].begin == 0:
             # input < 0 is impossible, since unicode codepoints start at 0!
             txt += __get_code(state,TriggerMap[MiddleTrigger_Idx:], LanguageDB, 
                                      StateMachineName, StateIdx, BackwardLexingF=BackwardLexingF)
        else:
            if middle[0].begin < 0:
                raise "code generation: error cannot split intervals at negative code points."

            txt += "$if input $< %s $then\n" % repr(middle[0].begin)
            txt += __get_code(state,TriggerMap[:MiddleTrigger_Idx], LanguageDB, 
                    StateMachineName, StateIdx, BackwardLexingF=BackwardLexingF)
            txt += "$end$else\n"
            txt += __get_code(state,TriggerMap[MiddleTrigger_Idx:], LanguageDB, 
                    StateMachineName, StateIdx, BackwardLexingF=BackwardLexingF)
            txt += "$end\n" 
        
    # return program text for given language
    return languages.replace_keywords(txt, LanguageDB, NoIndentF=False)


