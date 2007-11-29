import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
from copy import deepcopy


def do(LanguageDB, StateMachineName, state, StateIdx, BackwardLexingF):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    # (*) check that no epsilon transition triggers to a real state                   
    assert state.get_epsilon_target_state_indices() == [], \
           "epsilon transition contained target states: state machine was not made a DFA!\n" + \
           "epsilon target states = " + repr(state.get_epsilon_target_state_indices())
       
    #_________________________________________________________________________________________    
    TriggerMap = state.get_trigger_map()
    
    # note down information about success, if state is an acceptance state
    acceptance_info = LanguageDB["$acceptance-info"](state.get_origin_list(), LanguageDB, BackwardLexingF)
    code_str = ""
    if acceptance_info != "":
        code_str = "    " + acceptance_info.replace("\n", "\n    ")
        if code_str[-4:] == "    ": code_str = code_str[:-4]
    
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
        code_str += "    "
        if not BackwardLexingF: code_str += "%s\n" % LanguageDB["$input/get"] 
        else:                   code_str += "%s\n" % LanguageDB["$input/get-backwards"] 

        txt = __get_code(state,TriggerMap, LanguageDB, 
                         StateMachineName, StateIdx, 
                         BackwardLexingF = BackwardLexingF)

    else:
        empty_trigger_map_f = True
        # Empty State (no transitions, but the epsilon transition)
        txt  = "    "
        txt += "$/* no trigger set, no 'get character' $*/"

        # trigger outside the trigger intervals
        txt += "\n" + LanguageDB["$transition"](StateMachineName, StateIdx,
                                                state.is_acceptance(),
                                                None,
                                                state.get_origin_list(),
                                                BackwardLexingF                = BackwardLexingF, 
                                                BufferReloadRequiredOnDropOutF = False)
        txt += "\n"
        txt  = txt.replace("\n", "\n    ")

    code_str += txt + "\n"

    # -- drop out code (transition to no target state)
    drop_out_label = languages_label.get_drop_out(StateMachineName, StateIdx)
    txt  = LanguageDB["$label-definition"](drop_out_label) + "\n"
    txt += LanguageDB["$drop-out"](StateMachineName, StateIdx, BackwardLexingF,
                                   BufferReloadRequiredOnDropOutF = not empty_trigger_map_f,
                                   CurrentStateIsAcceptanceF      = state.is_acceptance(),
                                   OriginList                     = state.get_origin_list(),
                                   LanguageDB                     = LanguageDB)
        
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
            assert trigger_interval.begin == previous_interval.end, \
                   "non-adjacent intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            assert trigger_interval.end > previous_interval.begin, \
                   "unsorted intervals in TriggerMap\n" + \
                   "TriggerMap = " + repr(TriggerMap)
            previous_interval = deepcopy(trigger_interval)

        
    #________________________________________________________________________________
    txt = "    "

    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        txt += __create_transition_code(StateMachineName, StateIdx, state, TriggerMap[0], 
                                        LanguageDB, BackwardLexingF)
        
    else:    
        # two or more intervals => cut in the middle
        MiddleTrigger_Idx = int(TriggerSetN / 2)
        middle = TriggerMap[MiddleTrigger_Idx]

        if middle[0].begin == 0:
             # input < 0 is impossible, since unicode codepoints start at 0!
             txt += __get_code(state,TriggerMap[MiddleTrigger_Idx:], LanguageDB, 
                                      StateMachineName, StateIdx, BackwardLexingF=BackwardLexingF)

        elif TriggerSetN == 2:
             txt += __bracket_two_intervals(TriggerMap, StateMachineName, StateIdx, state,
                                            LanguageDB, BackwardLexingF)

        elif TriggerSetN == 3:
             txt += __bracket_three_intervals(TriggerMap, StateMachineName, StateIdx, state,
                                              LanguageDB, BackwardLexingF)

        else:
            txt += __bracket_normally(MiddleTrigger_Idx, TriggerMap, LanguageDB, 
                                      StateMachineName, StateIdx, state, BackwardLexingF)
        
    # return program text for given language
    return languages.replace_keywords(txt, LanguageDB, NoIndentF=False)

def __create_transition_code(StateMachineName, StateIdx, state, TriggerMapEntry, 
                             LanguageDB, BackwardLexingF, IndentF=False):
    """Creates the transition code to a given target based on the information in
       the trigger map entry.
    """
    interval           = TriggerMapEntry[0]
    target_state_index = TriggerMapEntry[1]       
    #  target state != None, then the machine is still eating
    #                        => transition to subsequent state.
    #
    #  target state == None, drop into a terminal state (defined by origins).
    #
    #  for details about $transition, see the __transition() function of the
    #  respective language module.
    #
    txt = "%s" % LanguageDB["$transition"](StateMachineName, 
                                           StateIdx,
                                           state.is_acceptance(),
                                           target_state_index,
                                           state.get_origin_list(),
                                           BackwardLexingF) 
    txt += "    $/* %s $*/" % interval.get_utf8_string()

    if IndentF: txt = "    " + txt.replace("\n", "\n    ")
    return txt
        
def __bracket_two_intervals(TriggerMap, StateMachineName, StateIdx, state,
                            LanguageDB, BackwardLexingF):
    assert len(TriggerMap) == 2

    first  = TriggerMap[0]
    second = TriggerMap[1]

    # If the first interval causes a 'drop out' then make it the second.
    # If the second interval is a 'drop out' the 'goto drop out' can be spared,
    # since it lands there anyway.
    # if second[0] < 0: # target state index < 0 ==> drop out
    #    tmp = first; first = second; second = tmp

    # find interval of size '1'
    first_interval  = first[0]
    second_interval = second[0]

    if   first_interval.size() == 1: 
        txt = "$if input $== %s $then\n" % repr(first_interval.begin)
    elif second_interval.size() == 1: 
        txt = "$if input $!= %s $then\n" % repr(second_interval.begin)
    else:                   
        txt = "$if input $< %s $then\n"  % repr(second_interval.begin)

    txt += __create_transition_code(StateMachineName, StateIdx, state, first, 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += "$end$else\n"
    txt += __create_transition_code(StateMachineName, StateIdx, state, second, 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += "$end\n" 

    return txt

def __bracket_three_intervals(TriggerMap, StateMachineName, StateIdx, state,
                              LanguageDB, BackwardLexingF):
    assert len(TriggerMap) == 3

    # does one interval have the size '1'?
    size_one_map = [False, False, False]   # size_on_map[i] == True if interval 'i' has size '1'
    for i in range(len(TriggerMap)):
        interval = TriggerMap[i][0]
        if interval.size() == 1: size_one_map[i] = True

    # (*) special trick only hold for one single case:
    #     -- the interval in the middle has size 1
    #     -- the outer two intervals trigger to the same target state
    target_state_0 = TriggerMap[0][1]
    target_state_2 = TriggerMap[2][1]
    if size_one_map != [False, True, False] or target_state_0 != target_state_2:
        return __bracket_normally(1, TriggerMap, LanguageDB, 
                                  StateMachineName, StateIdx, state, BackwardLexingF)

    # (*) test: inner character is matched => goto its target
    #           else:                      => goto alternative target
    txt = "$if input $== %s $then\n" % repr(TriggerMap[1][0].begin)
    txt += __create_transition_code(StateMachineName, StateIdx, state, TriggerMap[1], 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += "$end$else\n"
    # TODO: Add somehow a mechanism to report that here the intervals 0 **and** 1 are triggered
    #       (only for the comments in the generated code)
    txt += __create_transition_code(StateMachineName, StateIdx, state, TriggerMap[0], 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += "$end\n" 
    return txt

def __bracket_normally(MiddleTrigger_Idx, TriggerMap, LanguageDB, StateMachineName, StateIdx, state, BackwardLexingF):

    middle = TriggerMap[MiddleTrigger_Idx]
    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    txt  = "$if input $< %s $then\n" % repr(middle[0].begin)
    txt += __get_code(state,TriggerMap[:MiddleTrigger_Idx], LanguageDB, 
                      StateMachineName, StateIdx, BackwardLexingF)
    txt += "$end$else\n"
    txt += __get_code(state,TriggerMap[MiddleTrigger_Idx:], LanguageDB, 
                      StateMachineName, StateIdx, BackwardLexingF)
    txt += "$end\n" 

    return txt




