import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
from copy import deepcopy
__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

def do(LanguageDB, StateMachineName, state, StateIdx, BackwardLexingF, 
       BackwardInputPositionDetectionF=False, EndOfFile_Code=None):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    # (*) check that no epsilon transition triggers to a real state                   
    if __DEBUG_CHECK_ACTIVE_F:
        assert state.transitions().get_epsilon_target_state_index_list() == [], \
               "epsilon transition contained target states: state machine was not made a DFA!\n" + \
               "epsilon target states = " + repr(state.transitions().get_epsilon_target_state_index_list())
       
    #_________________________________________________________________________________________    
    TriggerMap = state.transitions().get_trigger_map()
    
    # note down information about success, if state is an acceptance state
    acceptance_info = LanguageDB["$acceptance-info"](state.origins().get_list(), 
                                                     LanguageDB, 
                                                     BackwardLexingF,
                                                     BackwardInputPositionDetectionF)
    if acceptance_info != "":
        code_str = acceptance_info
    
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       i.e states with no transition trigger map. If those can be avoided, then
    #       this variable can be replaced by 'True'
    drop_out_target_state_id = -1L
    if TriggerMap != []:
        empty_trigger_map_f = False

        input_label = languages_label.get_input(StateMachineName, StateIdx)
        code_str += LanguageDB["$label-definition"](input_label) + "\n"
        #
        code_str += "    "
        if not BackwardLexingF: code_str += "%s\n" % LanguageDB["$input/get"] 
        else:                   code_str += "%s\n" % LanguageDB["$input/get-backwards"] 

        code_str += "    " + LanguageDB["$debug-info-input"] + "\n"

        if len(TriggerMap) > 1:
            txt = __get_code(state,TriggerMap, LanguageDB, 
                             StateMachineName, StateIdx, 
                             BackwardLexingF = BackwardLexingF)
        else:
            # We cannot transit to any subsequent state without checking wether
            # the received character was a buffer limit code. To prevent an 
            # unconditional goto, rewrite the drop out in such a way that by
            # default it moves to the given target state. In case of buffer limit
            # code it returns in order to read the next character.
            txt = ""
            drop_out_target_state_id = TriggerMap[0][1]

    else:
        empty_trigger_map_f = True
        # Empty State (no transitions, but the epsilon transition)
        txt  = "    "
        txt += LanguageDB["$comment"]("no trigger set, no 'get character'") + "\n"

        # trigger outside the trigger intervals
        txt += LanguageDB["$transition"](StateMachineName, StateIdx, None,
                                         BackwardLexingF                = BackwardLexingF, 
                                         BufferReloadRequiredOnDropOutF = False)
        txt += "\n"
        txt  = txt.replace("\n", "\n    ")

    code_str += txt + "\n"

    # -- drop out code (transition to no target state)
    drop_out_label = languages_label.get_drop_out(StateMachineName, StateIdx)
    txt  = LanguageDB["$label-definition"](drop_out_label) + "\n"

    # -- in case of the init state, the end of file character has to be checked.
    if EndOfFile_Code != None and BackwardLexingF == False:
        txt += LanguageDB["$if =="]("0x%X" % EndOfFile_Code)

        txt += "    " + LanguageDB["$comment"](
                "/* NO CHECK: last_acceptance != -1 ? since the first state can **never** be an acceptance state") 
        txt += "\n"
        txt += "    " + LanguageDB["$transition"](StateMachineName, StateIdx, "END_OF_FILE", 
                                                  BackwardLexingF=False) + "\n"
        txt += LanguageDB["$end"] + "\n"

    txt += LanguageDB["$drop-out"](StateMachineName, StateIdx, BackwardLexingF,
                                   BufferReloadRequiredOnDropOutF = not empty_trigger_map_f,
                                   CurrentStateIsAcceptanceF      = state.is_acceptance(),
                                   OriginList                     = state.origins().get_list(),
                                   LanguageDB                     = LanguageDB,
                                   DropOutTargetStateID           = drop_out_target_state_id)
        
    txt = txt.replace("\n", "\n    ")
    code_str += txt + "\n"

    return code_str # languages.replace_keywords(code_str, LanguageDB, NoIndentF=True)

def __get_code(state, TriggerMap, LanguageDB, StateMachineName, StateIdx, BackwardLexingF):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    TriggerSetN = len(TriggerMap)

    if TriggerSetN > 1 and __DEBUG_CHECK_ACTIVE_F:
        # -- check that the trigger map consist of sorted adjacent intervals 
        #    This assumption is critical because it is assumed that for any isolated
        #    interval the bordering intervals have bracketed the remaining cases!
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
        

    # (*) indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    if txt[-1] == "\n": txt = txt[:-1]
    txt = txt.replace("\n", "\n    ") + "\n"
    return txt 

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
    txt =  "    " + LanguageDB["$transition"](StateMachineName, StateIdx, target_state_index, 
                                              BackwardLexingF) 
    txt += "    " + LanguageDB["$comment"](interval.get_utf8_string()) + "\n"

    if IndentF: 
        txt = txt[:-1].replace("\n", "\n    ") + "\n" # don't replace last '\n'
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
        txt = LanguageDB["$if =="](repr(first_interval.begin))
    elif second_interval.size() == 1: 
        txt = LanguageDB["$if !="](repr(second_interval.begin))
    else:                   
        txt = LanguageDB["$if <"](repr(second_interval.begin))

    txt += __create_transition_code(StateMachineName, StateIdx, state, first, 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += LanguageDB["$endif-else"]
    txt += __create_transition_code(StateMachineName, StateIdx, state, second, 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += LanguageDB["$end-else"]

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
    txt = LanguageDB["$if =="](repr(TriggerMap[1][0].begin))
    txt += __create_transition_code(StateMachineName, StateIdx, state, TriggerMap[1], 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += LanguageDB["$endif-else"]
    # TODO: Add somehow a mechanism to report that here the intervals 0 **and** 1 are triggered
    #       (only for the comments in the generated code)
    txt += __create_transition_code(StateMachineName, StateIdx, state, TriggerMap[0], 
                                    LanguageDB, BackwardLexingF, IndentF=True)
    txt += LanguageDB["$end-else"]
    return txt

def __bracket_normally(MiddleTrigger_Idx, TriggerMap, LanguageDB, StateMachineName, StateIdx, state, BackwardLexingF):

    middle = TriggerMap[MiddleTrigger_Idx]
    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    txt =  LanguageDB["$if <"](repr(middle[0].begin))
    txt += __get_code(state,TriggerMap[:MiddleTrigger_Idx], LanguageDB, 
                      StateMachineName, StateIdx, BackwardLexingF)
    txt += LanguageDB["$endif-else"]
    txt += __get_code(state,TriggerMap[MiddleTrigger_Idx:], LanguageDB, 
                      StateMachineName, StateIdx, BackwardLexingF)
    txt += LanguageDB["$end-else"]

    return txt




