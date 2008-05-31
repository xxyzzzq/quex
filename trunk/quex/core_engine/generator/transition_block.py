import sys

__DEBUG_CHECK_ACTIVE_F = False # Use this flag to double check that intervals are adjacent

def do(state, StateIdx, TriggerMap, LanguageDB, InitStateF, BackwardLexingF, StateMachineName):
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       i.e states with no transition trigger map. If those can be avoided, then
    #       this variable can be replaced by 'True'
    txt = ""
    if TriggerMap != []:

        if len(TriggerMap) > 1:
            txt = __get_code(state, TriggerMap, LanguageDB, 
                             StateMachineName, StateIdx, 
                             BackwardLexingF = BackwardLexingF)
        else:
            # We can actually be sure, that the Buffer Limit Code is filtered
            # out, since this is the task of the regular expression parser.
            # In case of backward lexing in pseudo-ambiguous post conditions,
            # it makes absolutely sense that there is only one interval that
            # covers all characters (see the discussion there).
            assert TriggerMap[0][0].begin == -sys.maxint
            assert TriggerMap[0][0].end   == sys.maxint
            txt =  "    " + LanguageDB["$transition"](StateMachineName, 
                                                      StateIdx, 
                                                      TriggerMap[0][1], 
                                                      BackwardLexingF) 

    else:
        # Empty State (no transitions, but the empty epsilon transition)
        txt  = "    "
        txt += LanguageDB["$comment"]("no trigger set, no 'get character'") + "\n"

        # trigger outside the trigger intervals
        txt += LanguageDB["$transition"](StateMachineName, StateIdx, None,
                                         BackwardLexingF                = BackwardLexingF, 
                                         BufferReloadRequiredOnDropOutF = False)
        txt += "\n"
        txt  = txt.replace("\n", "\n    ")

    return txt + "\n"

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
    #     -- if the special trick cannot be applied than bracket normally
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





