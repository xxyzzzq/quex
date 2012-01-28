import quex.engine.generator.state.transition.code      as transition_code
import quex.engine.generator.state.transition.solution  as solution
import quex.engine.generator.state.transition.bisection as bisection
from   quex.engine.interval_handling                          import Interval
from   quex.blackboard                                        import E_EngineTypes, \
                                                                     E_StateIndices, \
                                                                     setup as Setup
import sys
from   copy      import copy
from   operator  import itemgetter
from   itertools import imap

LanguageDB = None

def debug(TransitionMap, Function):
    print "##--BEGIN %s" % Function
    for entry in TransitionMap:
        print "##", entry[0]
    print "##--END %s" % Function

def do(txt, TransitionMap, 
       StateIndex     = None,  
       EngineType     = E_EngineTypes.FORWARD, 
       InitStateF     = False, 
       GotoReload_Str = None, 
       TheAnalyzer    = None,
       SuppressDebugStateOutputF = False):
    global LanguageDB
    assert isinstance(TransitionMap, list)
    assert EngineType        in E_EngineTypes
    assert isinstance(InitStateF, bool)
    assert StateIndex        is None or isinstance(StateIndex, long)
    assert GotoReload_Str    is None or isinstance(GotoReload_Str, (str, unicode))

    assert_adjacency(TransitionMap)

    LanguageDB = Setup.language_db

    if not SuppressDebugStateOutputF:
        LanguageDB.STATE_DEBUG_INFO(txt, StateIndex, (InitStateF and EngineType == E_EngineTypes.FORWARD))

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
                                                     GotoReload_Str, TheAnalyzer)) 
                       for entry in TransitionMap ]

    __get_code(txt, transition_map)

def __get_code(txt, TriggerMap):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    global LanguageDB

    T   = len(txt)
    N   = len(TriggerMap)
    tip = solution.get(TriggerMap)

    if   tip == solution.E_Type.TRANSITION:          __create_transition_code(txt, TriggerMap[0], IndentF=True)
    elif tip == solution.E_Type.UPPER_ONLY:          __get_code(txt, TriggerMap[int(N/2):]) 
    elif tip == solution.E_Type.OUTSTANDING:         __get_outstanding(txt, TriggerMap) 
    elif tip == solution.E_Type.SWITCH_CASE:         __get_switch(txt, TriggerMap)
    elif tip == solution.E_Type.BISECTION:           __get_bisection(txt, TriggerMap)
    elif tip == solution.E_Type.COMPARISON_SEQUENCE: __get_comparison_sequence(txt, TriggerMap)
    else:                                                                 
        assert False

    # (*) Indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    LanguageDB.INDENT(txt, Start=T)

def __get_outstanding(txt, TriggerMap, EntryIndex):
    """Implements the remaining transitions as:

       (1) Check for an exceptionally often character
       (2) Check for the remaining trigger map
    """
    assert TriggerMap[EntryIndex].size() == 1
    OutstandingCharacter = TriggerMap[EntryIndex].begin

    if EntryIndex != 0 and EntryIndex != len(TriggerMap) - 1:
        # Leave the entry before at size '1' because its easier to test
        if   TriggerMap[EntryIndex-1].size() == 1: TriggerMap[EntryIndex+1].begin = OutstandingCharacter
        else:                                      TriggerMap[EntryIndex-1].end   = OutstandingCharacter + 1
    elif EntryIndex == 0:
        TriggerMap[EntryIndex+1].begin = OutstandingCharacter
    elif EntryIndex == len(TriggerMap) - 1:
        TriggerMap[EntryIndex-1].begin = OutstandingCharacter

    txt.append(LanguageDB.IF_INPUT("==", OutstandingCharacter))
    __create_transition_code(txt, TriggerMap[EntryIndex])
    txt.append(LanguageDB.ELSE)
    __get_code(txt, TriggerMap)
    txt.append(LanguageDB.ENDIF)

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
    global LanguageDB

    case_code_list = []
    for interval, target in TriggerMap:
        if target.drop_out_f: continue
        target_code = []
        __create_transition_code(target_code, (interval, target))
        case_code_list.append((range(interval.begin, interval.end), target_code))

    txt.extend(LanguageDB.SELECTION("input", case_code_list))
    txt.append("\n")
    return True

def __get_bisection(txt, TriggerMap):
    LanguageDB = Setup.language_db

    BisectionIndex = bisection.get_index(TriggerMap)

    lower  = TriggerMap[:BisectionIndex]
    higher = TriggerMap[BisectionIndex:]

    assert len(lower) != 0
    assert len(higher) != 0

    HighBegin = higher[0][0].begin
    LowBegin  = lower[0][0].begin

    def is_only_drop_out(X):
        """RETURN: True, if all intervals (actually n==1) in X only transit 
                   to DROP_OUT."""
        return len(X) == 1 and X[0][1].drop_out_f

    def is_single_character(X):
        """RETURN: True, if interval of X transits on a single character."""
        return len(X) == 1 and X[0][0].size() == 1

    def get_if_statement(InverseF=False):
        if not InverseF:
            # If the size of one interval is 1, then replace the '<' by an '=='.
            if   is_single_character(lower):  return LanguageDB.IF_INPUT("==", LowBegin)
            elif is_single_character(higher): return LanguageDB.IF_INPUT("!=", HighBegin)
            else:                             return LanguageDB.IF_INPUT("<",  HighBegin)
        else:
            # If the size of one interval is 1, then replace the '>=' by an '=='.
            if   is_single_character(lower):  return LanguageDB.IF_INPUT("!=", LowBegin)
            elif is_single_character(higher): return LanguageDB.IF_INPUT("==", HighBegin)
            else:                             return LanguageDB.IF_INPUT(">=", HighBegin)

    # Note, that an '<' does involve a subtraction. A '==' only a comparison.
    # The latter is safe to be faster (or at least equally fast) on any machine.
    txt.append(0)
    if is_only_drop_out(higher):
        txt.append(get_if_statement())
        __get_code(txt, lower)
        # No 'else' case for what comes BEHIND middle => drop_out
    elif is_only_drop_out(lower):
        txt.append(get_if_statement(InverseF=True))
        __get_code(txt, higher)
        # No 'else' case for what comes BEFORE middle => drop_out
    else:
        txt.append(get_if_statement())
        __get_code(txt, lower)
        txt.append(0)
        txt.append(LanguageDB.ELSE)
        __get_code(txt, higher)

    txt.append(0)
    txt.append(LanguageDB.END_IF())

def __get_comparison_sequence(txt, TriggerMap):
    global LanguageDB

    L = len(TriggerMap)
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
    L = len(trigger_map)

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
            __create_transition_code(txt, entry, IndentF=True)

    txt.append("\n")
    txt.append(LanguageDB.END_IF(LastF=True))
    return True

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

def __prune_character_range(transition_map):
    assert len(transition_map) != 0

    LowerLimit = 0
    UpperLimit = Setup.get_character_value_limit()

    if UpperLimit == -1: return transition_map

    # (*) Delete any entry that lies out of bounds
    i    = 0
    size = len(transition_map)
    while i < size:
        interval, target = transition_map[i]
        if   interval.end < LowerLimit: 
            del transition_map[i]
            size -= 1
        elif interval.begin >= UpperLimit:
            del transition_map[i]
            size -= 1
        else:
            if interval.begin < LowerLimit: interval.begin = LowerLimit
            if interval.end   > UpperLimit: interval.end   = UpperLimit
            i += 1

def __create_transition_code(txt, TriggerMapEntry, IndentF=False):
    global LanguageDB

    if IndentF:
        txt.append(1)  # indent one scope

    code = TriggerMapEntry[1].code
    if type(code) == list: txt.extend(code)
    else:                  txt.append(code)

    if Setup.comment_transitions_f: 
        interval = TriggerMapEntry[0] 
        LanguageDB.COMMENT(txt, interval.get_utf8_string())
    else: 
        txt.append("\n")
    return 

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

