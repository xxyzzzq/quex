import quex.engine.generator.state_coder.transition_code as     transition_code
from   quex.engine.interval_handling                     import Interval
from   quex.engine.state_machine.state_core_info         import E_EngineTypes
from   quex.blackboard                                   import E_StateIndices, \
                                                                 setup as Setup
import sys
from   math      import log
from   copy      import copy
from   operator  import itemgetter
from   itertools import imap

def do(txt, TransitionMap, 
       StateIndex       = None,  EngineType     = E_EngineTypes.FORWARD, 
       InitStateF       = False, 
       ReturnToState_Str= None,  GotoReload_Str = None):
    assert isinstance(TransitionMap, list)
    assert EngineType        in E_EngineTypes
    assert isinstance(InitStateF, bool)
    assert StateIndex        is None or isinstance(StateIndex, (int, long))
    assert ReturnToState_Str is None or isinstance(ReturnToState_Str, (str, unicode))
    assert GotoReload_Str    is None or isinstance(GotoReload_Str, (str, unicode))
    assert_adjacency(TransitionMap)

    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       AND states during backward input position detection!
    if len(TransitionMap) == 0: return 


    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    __prune_character_range(TransitionMap)

    # The 'buffer-limit-code' always needs to be identified separately.
    # This helps to generate the reload procedure a little more elegantly.
    # (Backward input position detection does not reload. It only moves 
    #  inside the current lexeme, which must be inside the buffer.)
    if EngineType != E_EngineTypes.BACKWARD_INPUT_POSITION:
        __separate_buffer_limit_code_transition(TransitionMap, EngineType)

    # All transition information related to intervals become proper objects of 
    # class TransitionCode.
    transition_map = [ (entry[0], transition_code.do(entry[1], StateIndex, InitStateF, EngineType, 
                                                     ReturnToState_Str, GotoReload_Str)) 
                       for entry in TransitionMap ]

    txt.extend(__get_code(transition_map))

def __get_code(TriggerMap):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    LanguageDB = Setup.language_db
    TriggerSetN = len(TriggerMap)

    #________________________________________________________________________________

    txt = []
    if TriggerSetN == 1 :
        # (*) Only one interval 
        #     (all boundaring cases must have been dealt with already => case is clear)
        #     If the input falls into this interval the target trigger is identified!
        __create_transition_code(txt, TriggerMap[0][1])
        
    else:    
        # two or more intervals => cut in the middle
        MiddleTrigger_Idx = int(TriggerSetN / 2)
        middle            = TriggerMap[MiddleTrigger_Idx]

        # input < 0 is impossible, since unicode codepoints start at 0!
        if middle[0].begin == 0: 
            txt = __get_code(TriggerMap[MiddleTrigger_Idx:]) 
        else: 
            if   __get_switch(txt, TriggerMap):    pass
            elif __get_bisection(txt, TriggerMap): pass

    # (*) indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    LanguageDB.INDENT(txt)
    return txt

def __get_bisection(txt, TriggerMap):
    L = len(TriggerMap)
    preferred_section_index = int(L / 2)
    section_index           = preferred_section_index

    # Make sure that no cut in the middle of a switch case
    preferred_section_index = int(L / 2)
    best_section_index      = -1
    best_dist               = L
    switch_case_range_list  = __get_switch_cases_info(TriggerMap)
    for candidate in xrange(L):
        for p, q in switch_case_range_list:
            if candidate >= p and candidate <= q: 
                break
        else:
            # No intersection happened, so index may be used
            if abs(candidate - preferred_section_index) >= best_dist: continue
            best_section_index = candidate
            best_dist          = abs(candidate - preferred_section_index)

    if best_section_index not in [-1, 0, L-1]: section_index = best_section_index
    else:                                      section_index = preferred_section_index; 

    if __get_linear_comparison_chain(txt, TriggerMap, L): return True

    middle = TriggerMap[section_index]
    lower  = TriggerMap[:section_index]
    higher = TriggerMap[section_index:]

    assert middle[0].begin >= 0, \
           "code generation: error cannot split intervals at negative code points."

    __get_bisection_code(txt, middle, lower, higher)
    return True

def __get_linear_comparison_chain(txt, TriggerMap, L):

    LanguageDB = Setup.language_db
    # 5 intervals --> 4 border checks
    if L > 5: return False
    assert L != 1

    trigger_map = TriggerMap

    # Depending on whether the list is checked forward or backward,
    # the comparison operator and considered border may change.
    _border_cmp = "<"
    _border     = lambda interval: interval.end

    # The buffer limit code is something extreme seldom, so make sure that it is 
    # tested at last, if it is there. This might require to reverse the trigger map.
    if     Setup.buffer_limit_code >= TriggerMap[0][0].begin \
       and Setup.buffer_limit_code < TriggerMap[-1][0].end:
        # Find the index of the buffer limit code in the list
        for i, candidate in enumerate(TriggerMap):
            if candidate[0].contains(Setup.buffer_limit_code): break
        if i < L / 2:
            trigger_map = copy(TriggerMap)
            trigger_map.reverse()
            _border_cmp = ">="
            _border     = lambda interval: interval.begin

    assert len(trigger_map) != 0

    #txt.append("/*\n")
    #for interval, target in trigger_map:
    #    txt.append(" * [%04X, %04X) --> %s\n" % (interval.begin, interval.end, repr(target)))
    #txt.append("*/\n")

    LastI = L - 1
    for i, entry in enumerate(trigger_map):
        interval, target = entry

        txt.append("\n")
        txt.append(0)
        if   i == LastI:
            txt.append(LanguageDB.ELSE)
        elif interval.size() == 1:
            txt.append(LanguageDB.IF_INPUT("==", interval.begin, i==0))
        else:
            txt.append(LanguageDB.IF_INPUT(_border_cmp, _border(interval), i==0))

        if not target.drop_out_f:
            __create_transition_code(txt, entry[1])

    txt.append("\n")
    txt.append(LanguageDB.END_IF(LastF=True))
    return True

def __get_bisection_code(txt, middle, lower, higher):
    LanguageDB = Setup.language_db

    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    txt.append(0)
    if len(higher) == 1 and higher[0][1].drop_out_f:
        
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("==", lower[0][0].begin)
        elif higher[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("!=", higher[0][0].begin)
        else:
            if_statement = LanguageDB.IF_INPUT("<",  higher[0][0].begin)

        # No 'else' case for what comes BEHIND middle
        txt.append(if_statement)
        txt.extend(__get_code(lower))

    elif len(lower) == 1 and lower[0][1].drop_out_f:
        if   lower[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("!=", lower[0][0].begin)
        elif len(higher) == 1 and higher[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("==", higher[0][0].begin)
        else:
            if_statement = LanguageDB.IF_INPUT(">=", lower[0][0].end)

        # No 'else' case for what comes BEFORE middle
        txt.append(if_statement)
        txt.extend(__get_code(higher))

    else:
        # If the size of one interval is 1, then replace the '<' by an '=='.
        if   len(lower)  == 1 and lower[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("==", lower[0][0].begin)
        elif len(higher) == 1 and higher[0][0].size() == 1:
            if_statement = LanguageDB.IF_INPUT("!=", higher[0][0].begin)
        else:
            if_statement = LanguageDB.IF_INPUT("<",  middle[0].begin)

        txt.append(if_statement)
        txt.extend(__get_code(lower))
        txt.append(0)
        txt.append(LanguageDB.ELSE)
        txt.extend(__get_code(higher))

    txt.append(0)
    txt.append(LanguageDB.END_IF())

def __create_transition_code(txt, TriggerMapEntry):
    txt.append(1)                              # indent one scope
    txt.extend(TriggerMapEntry.code)
    # if Setup.buffer_codec == "": txt.append("    " + LanguageDB["$comment"](interval) + "\n")
    # else:                        txt.append("\n")
    return 

def __get_switch(txt, TriggerMap):
    """Transitions of characters that lie close to each other can be very efficiently
       be identified by a switch statement. For example:

           switch( Value ) {
           case 1: ..
           case 2: ..
           ...
           case 100: ..
           }

       Is implemented by the very few lines in assembler (i386): 

           sall    $2, %eax
           movl    .L13(%eax), %eax
           jmp     *%eax

       where 'jmp *%eax' jumps immediately to the correct switch case.
    
       It is therefore of vital interest that those regions are **identified** and
       **not split** by a bisection. To achieve this, such regions are made a 
       transition for themselves based on the character range that they cover.
    """
    LanguageDB = Setup.language_db

    drop_out_range_n = 0
    character_n      = 0
    for interval, target in TriggerMap:
        if target.drop_out_f: drop_out_range_n += 1
        else:                 character_n      += interval.size()

    if __switch_case_heuristic(TriggerMap) == False:
        return False

    case_code_list = []
    for interval, target in TriggerMap:
        if target.drop_out_f: continue
        target_code = target.code
        for i in range(interval.begin, interval.end):
            case_code_list.append((i, target_code))

    txt.extend(LanguageDB.SELECTION("input", case_code_list))
    return True

def __get_switch_cases_info(TriggerMap):
    L = len(TriggerMap)
    sum_interval_size          = [0] * (L+1)
    sum_drop_out_interval_size = [0] * (L+1)
    i = 0
    for interval, target in TriggerMap:
        i += 1
        sum_interval_size[i]          = sum_interval_size[i-1]
        sum_drop_out_interval_size[i] = sum_drop_out_interval_size[i-1]
        if target.drop_out_f: sum_drop_out_interval_size[i] += interval.size()
        else:                    sum_interval_size[i]          += interval.size()

    switch_case_range_list = []
    p = 0
    while p < L:
        # Count from the back, so the longest is treated first.
        # Thus, if there is a 'p' for a given 'q' where the criteria
        # holds for a switch case, then the 'p' is the best one, in the
        # sense that it is the largest interval.
        q_found = None
        for q in xrange(L-1, p, -1):
            if __switch_case_heuristic(TriggerMap[p:q+1], 
                                       size_all_intervals          = sum_interval_size[q]          - sum_interval_size[p],
                                       size_all_drop_out_intervals = sum_drop_out_interval_size[q] - sum_drop_out_interval_size[p]):
                switch_case_range_list.append((p, q))
                q_found = q
                break
        # If there was a switch case range, that step over it to the next
        if q_found: p = q_found
        p += 1
    return switch_case_range_list

def __switch_case_heuristic(TriggerMap, 
                            size_all_intervals=None, 
                            size_all_drop_out_intervals=None):
    """Let P be the preferably of a switch statement over bisection or linear if-else
       blocks. The following heuristics may be applied:
    
       -- The more ranges are involved in a trigger map, the more 'if-else' we need,
          thus:
                   P increases with len(trigger_map)

          Since only for bisection only log2(N) comparisons are necessary (and if linear
          if-else blocks are used, then only if N/2 < log2(N)), it may be assumed that

              (1)  P increases with log2(len(trigger_map))            

       -- The look-up tables used for switches can potentially grow large, so that

                   P decreases with size(trigger_map)

          where size(trigger_map) = all characters minus the ones that 'drop-out', thus
           
              (2)  P decreases with size(all intervals) - size(all drop out intervals)
               

       The following heuristic is proposed:

              P = log2(len(trigger_map)) / sum(all interval) - sum(drop_out_intervals) 
    """
    if size_all_intervals is None:
        size_all_intervals          = 0
        size_all_drop_out_intervals = 0
        for interval, target in TriggerMap:
            if target.drop_out_f: size_all_drop_out_intervals += interval.size()
            size_all_intervals += interval.size()

    if size_all_intervals - size_all_drop_out_intervals == 0:
        return False

    p = log(len(TriggerMap), 2) / (size_all_intervals - size_all_drop_out_intervals)

    return p > 0.03

def __separate_buffer_limit_code_transition(TransitionMap, EngineType):
    """This function ensures, that the buffer limit code is separated 
       into a single value interval. Thus the transition map can 
       transit immediate to the reload procedure.
    """
    BLC = Setup.buffer_limit_code
    for i, entry in enumerate(TransitionMap):
        interval, target_index = entry

        if   target_index == E_StateIndices.RELOAD_PROCEDURE:   
            assert interval.contains_only(Setup.buffer_limit_code) 
            assert EngineType != E_EngineTypes.BACKWARD_INPUT_POSITION
            # Transition 'buffer limit code --> E_StateIndices.RELOAD_PROCEDURE' 
            # has been setup already.
            return

        elif target_index is not E_StateIndices.DROP_OUT: 
            continue

        elif not interval.contains(Setup.buffer_limit_code): 
            continue

        # Found the interval that contains the buffer limit code.
        # If the interval's size is alread 1, then there is nothing to be done
        if interval.size() == 1: return

        before_begin = interval.begin
        before_end   = BLC
        after_begin  = BLC + 1 
        after_end    = interval.end

        # Replace Entry with (max.) three intervals: before, buffer limit code, after
        del TransitionMap[i]

        if after_end > after_begin:
            TransitionMap.insert(i, (Interval(after_begin, after_end), E_StateIndices.DROP_OUT))

        # "Target == E_StateIndices.RELOAD_PROCEDURE" => Buffer Limit Code
        TransitionMap.insert(i, (Interval(BLC, BLC + 1), E_StateIndices.RELOAD_PROCEDURE))

        if before_end > before_begin and before_end > 0:
            TransitionMap.insert(i, (Interval(before_begin, before_end), E_StateIndices.DROP_OUT))
        return

    # Any transition map, except for backward input position detection, 
    # must have a trigger on reload.
    assert EngineType in [E_EngineTypes.BACKWARD_INPUT_POSITION, E_EngineTypes.INDENTATION_COUNTER], \
           "Engine types other than 'backward input position detection' or 'indentation counter' must contain BLC.\n" \
           "Found: %s" % repr(EngineType)
    return

def __prune_character_range(TransitionMap):
    assert len(TransitionMap) != 0

    LowerLimit = 0
    UpperLimit = Setup.get_character_value_limit()

    if UpperLimit == -1: return TransitionMap

    # (*) Delete any entry that lies completely below the lower limit
    for i, entry in enumerate(TransitionMap):
        interval, target = entry
        if interval.end >= LowerLimit: break
    if i != 0: del TransitionMap[:i]

    if TransitionMap[0][0].begin < LowerLimit:
        TransitionMap[0][0].begin = LowerLimit

    # (*) Delete any entry that lies completely above the upper limit
    for i, entry in enumerate(reversed(TransitionMap)):
        interval, target = entry
        if interval.begin <= UpperLimit: break
    if i != 0: TransitionMap[len(TransitionMap) - i:]

    if TransitionMap[-1][0].end < UpperLimit + 1:
        TransitionMap[-1][0].end = UpperLimit + 1

def assert_adjacency(TransitionMap, TotalRangeF=False):
    """Check that the trigger map consist of sorted adjacent intervals 
       This assumption is critical because it is assumed that for any isolated
       interval the bordering intervals have bracketed the remaining cases!
    """
    if len(TransitionMap) == 0: return
    iterable = TransitionMap.__iter__()
    if TotalRangeF: previous_end = - sys.maxint
    else:           previous_end = iterable.next()[0].end 
    for interval in imap(itemgetter(0), iterable):
        assert interval.begin == previous_end # Intervals are adjacent!
        assert interval.end > interval.begin  # Interval size > 0! 
        previous_end = interval.end

    assert (not TotalRangeF) or TransitionMap[-1][0].end == sys.maxint
