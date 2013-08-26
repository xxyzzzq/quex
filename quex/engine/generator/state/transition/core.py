from   quex.engine.generator.state.transition.code      import TransitionCodeFactory
from   quex.engine.generator.state.entry_action         import DoorID_DROP_OUT
import quex.engine.generator.state.transition.solution  as     solution
import quex.engine.generator.state.transition.bisection as     bisection
import quex.engine.analyzer.engine_supply_factory       as     engine
from   quex.engine.analyzer.transition_map              import TransitionMap
from   quex.blackboard                                  import setup as Setup, E_StateIndices
from   copy      import copy
from   itertools import islice

LanguageDB = None

def do(txt, TM):
    global LanguageDB
    LanguageDB = Setup.language_db

    if len(TM) == 0:
        return

    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    TM.prune(0, Setup.get_character_value_limit())

    # (*) Determine 'outstanding' characters. For example, if 'e' appears
    #     exceptionally often, then it makes sense to check:
    #
    #     if( input == 'e' ) {
    #         ...
    #     } else {
    #         /* Rest of transition map. */
    #     }
    #     (Currently, this is a 'no-operation'. It is planned to consider
    #      statitistics about character occurencies into the generation of
    #      the transition map.)
    outstanding_list = solution.prune_outstanding(TM) 
    if outstanding_list is not None: 
        __get_outstanding(txt, outstanding_list)

    # (*) Bisection until other solution is more suitable.
    #     (This may include 'no bisectioning')
    # print "#TM:\n", TM.get_string(Option="hex")
    __bisection(txt, TM)

    # (*) When there was an outstanding character, then the whole bisection was
    #     implemented in an 'ELSE' block which must be closed.
    if outstanding_list is not None: 
        txt.append(LanguageDB.ENDIF)

def prepare_transition_map(TM, 
                           StateIndex     = None,
                           InitStateF     = False,
                           GotoReload_Str = None,
                           TheAnalyzer    = None,
                           EngineType     = engine.FORWARD):
    global LanguageDB
    assert isinstance(TM, list)
    assert TheAnalyzer is not None or isinstance(EngineType, engine.Base)
    assert isinstance(InitStateF, bool)
    assert StateIndex  is None     or isinstance(StateIndex, long)

    if TheAnalyzer is not None:
        EngineType = TheAnalyzer.engine_type

    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       AND states during backward input position detection!
    if len(TM) == 0: 
        return TM

    TM.assert_continuity()
    TM.fill_gaps(DoorID_DROP_OUT)

    goto_reload_str = TransitionCodeFactory.prepare_reload_tansition(TM,
                                     StateIndex,
                                     EngineType     = EngineType,
                                     InitStateF     = InitStateF,
                                     GotoReload_Str = GotoReload_Str)

    TransitionCodeFactory.init(EngineType, 
                               StateIndex    = StateIndex,
                               InitStateF    = InitStateF,
                               GotoReloadStr = goto_reload_str,
                               TheAnalyzer   = TheAnalyzer)

    return TransitionMap.from_iterable(TM, TransitionCodeFactory.do)

class SubTriggerMap(object):
    """A trigger map that 'points' into a subset of a trigger map.
       Instead of creating whole new subsets, relate to the original
       trigger map and store 'begin' and 'end' of the new map.
    """
    __slots__ = ("__trigger_map", "__begin_i", "__end_i")

    def __init__(self, TriggerMap):
        self.__trigger_map = TriggerMap
        self.__begin_i     = 0
        self.__end_i       = len(TriggerMap) - 1

    def __getitem__(self, X):
        if isinstance(X, slice):
            result = SubTriggerMap(self.__trigger_map)
            result.__begin_i = self.__begin_i + X.start
            result.__end_i   = self.__begin_i + X.stop
        else:
            return self.__trigger_map[self.__begin_i + X]

    def __len__(self):
        return self.__end_i - self.__begin_i

    def __iter__(self):
        for x in islice(self.__trigger_map, self.__begin_i, self.__end_i):
            yield x

    @property
    def middle(self):
        middle_i = int((self.__end_i - self.__begin_i) / 2) + self.__begin_i
        return self.__trigger_map[middle_i].begin

def debug(TM, Function):
    print "##--BEGIN %s" % Function
    for entry in TM:
        print "##", entry[0]
    print "##--END %s" % Function

def __bisection(txt, TriggerMap):
    """Creates code for state transitions from this state. This function is very
       similar to the function creating code for a 'NumberSet' condition 
       (see 'interval_handling').
    
       Writes code that does a mapping according to 'binary search' by
       means of if-else-blocks.
    """
    global LanguageDB

    T   = len(txt)
    tip = solution.get(TriggerMap)

    # Potentially Recursive
    if   tip == solution.E_Type.BISECTION:           __get_bisection(txt, TriggerMap)
    # Direct Implementation / No more call to __bisection()
    elif tip == solution.E_Type.SWITCH_CASE:         __get_switch(txt, TriggerMap)
    elif tip == solution.E_Type.COMPARISON_SEQUENCE: __get_comparison_sequence(txt, TriggerMap)
    elif tip == solution.E_Type.TRANSITION:          __get_transition(txt, TriggerMap[0], IndentF=True)
    else:                                                                 
        assert False

    # (*) Indent by four spaces (nested blocks are correctly indented)
    #     delete the last newline, to prevent additional indentation
    LanguageDB.INDENT(txt, Start=T)

def __get_outstanding(txt, TriggerMapEntry):
    txt.append(LanguageDB.IF_INPUT("==", TriggerMapEntry[0].begin))
    __get_transition(txt, TriggerMapEntry)
    txt.append(LanguageDB.ELSE)
    # Caller must provide later for 'ENDIF'

def __get_switch(txt, TriggerMap):
    """Transitions of characters that lie close to each other can be very efficiently
       be identified by a switch statement. For example:

           switch( Value ) {
           case 1: ..
           case 2: ..
           ...
           case 100: ..
           }

       If SwitchFrameF == False, then no 'switch() { ... }' frame is produced.

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
        __get_transition(target_code, (interval, target))
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
        __bisection(txt, lower)
        # No 'else' case for what comes BEHIND middle => drop_out
    elif is_only_drop_out(lower):
        txt.append(get_if_statement(InverseF=True))
        __bisection(txt, higher)
        # No 'else' case for what comes BEFORE middle => drop_out
    else:
        txt.append(get_if_statement())
        __bisection(txt, lower)
        txt.append(0)
        txt.append(LanguageDB.ELSE)
        __bisection(txt, higher)

    txt.append(0)
    txt.append(LanguageDB.END_IF())
    txt.append("\n")

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

        if i != 0: txt.append("\n")
        txt.append(0)
        if   i == LastI:
            txt.append(LanguageDB.ELSE)
        elif interval.size() == 1:
            txt.append(LanguageDB.IF_INPUT("==", interval.begin, i==0))
        else:
            txt.append(LanguageDB.IF_INPUT(_border_cmp, _border(interval), i==0))

        if not target.drop_out_f:
            __get_transition(txt, entry, IndentF=True)

    txt.append("\n")
    txt.append(0)
    txt.append(LanguageDB.END_IF(LastF=True))
    txt.append("\n")
    return True

def __get_transition(txt, TriggerMapEntry, IndentF=False):
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
        pass # txt.append("\n")
    return 

