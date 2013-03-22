"""____________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.generator.state.transition.code  import TransitionCodeFactory
import quex.engine.generator.state.transition.core  as     transition_block
import quex.engine.generator.state_machine_coder    as     state_machine_coder
import quex.engine.generator.state.transition.solution  as solution
from   quex.engine.generator.languages.address      import address_set_subject_to_routing_add
from   quex.engine.generator.base                   import get_combined_state_machine
from   quex.engine.generator.action_info            import CodeFragment
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
import quex.engine.analyzer.engine_supply_factory   as     engine
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.state_machine.index              as     index
from   quex.engine.interval_handling                import NumberSet, Interval
from   quex.engine.tools                            import print_callstack

from   quex.blackboard import setup as Setup, \
                              DefaultCounterFunctionDB, \
                              E_StateIndices

from   collections import defaultdict
from   copy        import deepcopy, copy
import re

def get(counter_db, Name):
    """Implement the default counter for a given Counter Database. 

    In case the line and column number increment cannot be determined before-
    hand, a something must be there that can count according to the rules given
    in 'counter_db'. This function generates the code for a general counter
    function which counts line and column number increments starting from the
    begin of a lexeme to its end.

    The implementation of the default counter is a direct function of the
    'counter_db', i.e. the database telling how characters influence the
    line and column number counting. If there is already a default counter
    for a counter_db that is equivalent, then it is not implemented a second 
    time. Instead, a reference to the first implementation is communicated.

    ---------------------------------------------------------------------------
    
    RETURNS: function_name, string --> function name and the implementation 
                                       of the function.
             function_name, None   --> function name of a function which has
                                       been implemented before, but serves
                                       the same purpose of counting for 
                                       'counter_db'.
    ---------------------------------------------------------------------------
    """
    function_name = DefaultCounterFunctionDB.get_function_name(counter_db)
    if function_name is not None:
        return function_name, None # Implementation has been done before.

    column_counter_per_chunk, state_machine_f, txt = get_step(counter_db, "iterator")

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(txt, function_name, state_machine_f, column_counter_per_chunk)
    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

Match_input    = re.compile("\\binput\\b", re.UNICODE)
Match_iterator = re.compile("\\iterator\\b", re.UNICODE)
def get_step(counter_db, IteratorName):

    tm, column_counter_per_chunk, state_machine_f = \
            get_counter_map(counter_db, IteratorName, 
                            Setup.buffer_codec_transformation_info)

    state_machine_f, txt, dummy = get_core_step(tm, IteratorName, state_machine_f)

    return column_counter_per_chunk, state_machine_f, txt

def get_core_step(TM, IteratorName, StateMachineF, BeforeGotoReloadAction=None):
    """Get a counter increment code for one single character.

    BeforeGotoReloadAction = None, means that there is no reload involed.

       RETURNS:
           [0]  -- True, if state machine was implemented.
                -- False, if not.
           [1]  -- source code implementing.
    """
    global Match_input
    global Match_iterator

    # The range of possible characters may be restricted. It must be ensured,
    # that the occurring characters only belong to the admissible range.
    transition_map_tool.prune(TM, 0, Setup.get_character_value_limit())

    if StateMachineF:
        upon_reload_done_adr = None

        txt = _trivialized_state_machine_coder_do(TM, BeforeGotoReloadAction)
        if txt is not None:
            StateMachineF = False # We tricked around it; No state machine needed.
        else:
            txt = _state_machine_coder_do(TM, BeforeGotoReloadAction)
    else:
        upon_reload_done_adr = index.get()
        address_set_subject_to_routing_add(upon_reload_done_adr) # Mark as 'used'

        txt = _transition_map_coder_do(TM, BeforeGotoReloadAction, upon_reload_done_adr)

    def replacer(block, StateMachineF):
        if block.find("(me->buffer._input_p)") != -1: 
            block = block.replace("(me->buffer._input_p)", IteratorName)
        if not StateMachineF:
            block = Match_input.sub("(*%s)" % IteratorName, block)
            block = Match_iterator.sub("(%s)" % IteratorName, block)
        return block

    for i, elm in enumerate(txt):
        if not isinstance(elm, (str, unicode)): continue
        txt[i] = replacer(elm, StateMachineF)

    return StateMachineF, txt, upon_reload_done_adr

def get_counter_dictionary(counter_db, ConcernedCharacterSet):
    """Returns a list of NumberSet objects where for each X of the list it holds:

         (i)  X is subset of ConcernedCharacterSet
               
         (ii) It is related to a different counter action than Y,
              for each other object Y in the list.

       RETURNS: 

                    list:    (character_set, count_action)
    """
    class Addition:
        __slots__ = ("value")
        def __init__(self, Value, Type):
            self.value = Value
            self.type  = Type

    def prune(X, ConcernedCharacterSet):
        if ConcernedCharacterSet is None:
            return X
        else:
            return X.intersection(ConcernedCharacterSet)

    result = []
    for delta, character_set in counter_db.special.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, Addition(delta, "column_add")))

    for grid_step_n, character_set in counter_db.grid.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, Addition(grid_step_n, "grid_step")))

    for delta, character_set in counter_db.newline.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, Addition(delta, "line_add")))

    return result

def get_counter_map(counter_db, 
                    IteratorName             = None,
                    Trafo                    = None,
                    ColumnCountPerChunk      = None,
                    ConcernedCharacterSet    = None,
                    DoNotResetReferenceP_Set = None):
    """Provide a map which associates intervals with counting actions, i.e.

           map: 
                    character interval --> count action

    The mapping is provided in the form of a transition map, i.e.  a list of
    sorted pairs of (interval, action).

    This function also determines whether a state machine is required to
    implement the count per character, or a single loop is enough.  If the
    length of the lexeme can be determined by the byte-number of the lexeme, a
    factor 'ColumnCountPerChunk' != None is returned.

    If ColumnCountPerChunk is specified as argument, it is assumed that it is
    correct.  It is conceivable that a state machine is required for walking
    along the lexeme, and to DETECT the end; The end may be beyond the
    character set of concern.

    ___________________________________________________________________________
    RETURNS: [0] counter map
             [1] not None --> ColumnCountPerChunk, where the specific opti-
                              mazation with the 'reference_p' has been applied.
                 None     --> No optimization with 'reference_p'.
             [2] True     --> State machine implementation required
                 False    --> Else.
    ___________________________________________________________________________

       counter_db -- Database with counting information based on 
                     character sets in UNICODE.

       ConcernedActionSet -- Pairs of (character_set, Actions) where
                             characters are specified in UNICODE.

               .-------------------------------------------------.
               | The resulting transition map is in the CODEC of |
               | 'Setup.buffer_codec_transformation_info'.       |
               |                                                 |
               |    -- if it is not a variable size codec --     |
               '-------------------------------------------------'

    'ConcernedActionSet' is the character set is actually concerned by
    the counting. If it is None, then all characters of the counter_db
    are considered. 

    'UndefinedCodePointAction' is the action that shall happen if the 
    transition map hits an undefined point.

    'AllowReferenceP_F' makes a special kind of optimization available.  It is
    applied in case that there is only one single value for column counts.
    Consider the figure below:

          ---- memory address --->
                                         later
                                         iterator
                                             |
          | | | | | | |*| | | | | | | | | | | | | | | | | | | | | |
                       |
                  reference_p 
                  = iterator

    The '*' stands for a 'grid' or a 'newline' character.  If such a character
    appears, the 'reference_p' is set to the current 'iterator'.  As long as no
    such character appears, the term to be added is proportional to 'iterator -
    reference_p'.  The counter implementation profits from this.  It does not
    increment the 'column_n' as long as only 'normal' characters appear.  It
    only adds the delta multiplied with a constant.

    The implementation of this mechanism is implemented by the functions
    '__special()', '__grid()', and '__newline()'.  It is controlled there by
    argument 'ColumnCountPerChunk'.  If it is not None, it happens to be the
    factor 'C' for the addition of 'C * (iterator - reference_p)'.
    ___________________________________________________________________________
    """
    # If ColumnCountPerChunk is None => no action depends on IteratorName. 
    # See '__special()', '__grid_step()', and '__line_n()'.

    counter_dictionary = get_counter_dictionary(counter_db, ConcernedCharacterSet)

    state_machine_f    = Setup.variable_character_sizes_f()
    
    if ColumnCountPerChunk is not None:
        # It *is* conceivable, that there is a subset of 'CharacterSet' which
        # can be handled with a 'column_count_per_chunk' and for all other
        # characters in 'CharacterSet' the user does something to make it fit
        # (see character set skipper, for example).
        column_count_per_chunk = ColumnCountPerChunk
    else:
        column_count_per_chunk = get_column_number_per_chunk(counter_db, 
                                                             ConcernedCharacterSet)

    def extend(result, number_set, action):
        interval_list = number_set.get_intervals(PromiseToTreatWellF=True)
        result.extend((x, action) for x in interval_list)

    def handle_grid_and_newline(cm, number_set, action, column_count_per_chunk, IteratorName, ResetReferenceP_F):
        if action.type == "grid_step":
            extend(cm, number_set, __grid_step(action.value, column_count_per_chunk, IteratorName, 
                                               ResetReferenceP_F=ResetReferenceP_F))

        elif action.type == "line_add":
            extend(cm, number_set, __line_n(action.value, column_count_per_chunk, IteratorName, 
                                            ResetReferenceP_F=ResetReferenceP_F))

    cm = []
    for number_set, action in counter_dictionary:
        if action.type == "column_add":
            if column_count_per_chunk is None:
                extend(cm, number_set, __special(action.value))
            else:
                # Column counts are determined by '(iterator - reference) * C'
                pass
            continue

        if DoNotResetReferenceP_Set is None or not DoNotResetReferenceP_Set.has_intersection(number_set):
            handle_grid_and_newline(cm, number_set, action, column_count_per_chunk, IteratorName, 
                                    ResetReferenceP_F=True)
        else:
            do_set   = number_set.difference(DoNotResetReferenceP_Set)
            handle_grid_and_newline(cm, do_set, action, column_count_per_chunk, IteratorName, 
                                    ResetReferenceP_F=True)

            dont_set = number_set.intersection(DoNotResetReferenceP_Set)
            handle_grid_and_newline(cm, dont_set, action, column_count_per_chunk, IteratorName, 
                                    ResetReferenceP_F=False)

    transition_map_tool.sort(cm)

    return cm, column_count_per_chunk, state_machine_f

def get_state_machine_list(TM, ReloadPossibleF=False):
    """Returns a state machine list which implements the transition map given
    in unicode. It is assumed that the codec is a variable
    character size codec. Each count action is associated with a separate
    state machine in the list. The association is recorded in 'action_db'.

    RETURNS: [0] -- The 'action_db': state_machine_id --> count action
             [1] -- The list of state machines. 
    """
    assert type(ReloadPossibleF) == bool

    # Sort by actions.
    action_code_db = defaultdict(NumberSet)
    for character_set, action_list in TM:
        action_code_db[tuple(action_list)].unite_with(character_set)

    # Make each action a terminal.
    sm_list   = []
    action_db = {}
    for action, trigger_set in action_code_db.iteritems():
        sm = StateMachine()
        if ReloadPossibleF and trigger_set.contains(Setup.buffer_limit_code):
            trigger_set.subtract(Interval(Setup.buffer_limit_code, 
                                          Setup.buffer_limit_code + 1))
        sm.add_transition(sm.init_state_index, trigger_set, AcceptanceF=True)
        sm_list.append(sm)
        action_db[sm.get_id()] = CodeFragment(list(action))

    return action_db, sm_list

def get_column_number_per_chunk(counter_db, CharacterSet):
    """Considers the counter database which tells what character causes
    what increment in line and column numbers. However, only those characters
    are considered which appear in the CharacterSet. 

    'CharacterSet' is None: All characters considered.

    If the special character handling column number increment always
    add the same value the return value is not None. Else, it is.

    RETURNS: None -- If there is no distinct column increment 
             >= 0 -- The increment of column number for every character
                     from CharacterSet.
    """
    result     = None
    number_set = None
    for delta, character_set in counter_db.special.iteritems():
        if CharacterSet is None or character_set.has_intersection(CharacterSet):
            if result is None: result = delta; number_set = character_set
            else:              return None

    if Setup.variable_character_sizes_f():
        result = transformation.homogeneous_chunk_n_per_character(number_set, 
                                                                  Setup.buffer_codec_transformation_info)
    return result

def get_grid_and_line_number_character_set(counter_db):
    result = NumberSet()
    for character_set in counter_db.grid.itervalues():
        result.unite_with(character_set)

    for character_set in counter_db.newline.itervalues():
        result.unite_with(character_set)
    return result

def _transition_map_coder_do(TM, BeforeGotoReloadAction, UponReloadDoneAdr):

    LanguageDB = Setup.language_db

    txt = []
    if BeforeGotoReloadAction is not None:
        assert isinstance(UponReloadDoneAdr, (int, long))
        engine_type = engine.FORWARD
        #index = transition_map_tool.index(TransitionMap, Setup.buffer_limit_code)
        #assert index is not None
        #assert TransitionMap[index][1] == E_StateIndices.DROP_OUT
        goto_reload_action = copy(BeforeGotoReloadAction)
        goto_reload_action.append(LanguageDB.GOTO_RELOAD(UponReloadDoneAdr, True, engine_type))
        goto_reload_str    = "".join(goto_reload_action)
        transition_map_tool.set(TM, Setup.buffer_limit_code, goto_reload_str)
    else:
        engine_type     = engine.CHARACTER_COUNTER
        goto_reload_str = None


    TransitionCodeFactory.init(engine_type, 
                               StateIndex    = None,
                               InitStateF    = True,
                               GotoReloadStr = goto_reload_str,
                               TheAnalyzer   = None)
    tm = [ 
        (interval, TransitionCodeFactory.do(x)) for interval, x in TM 
    ]

    LanguageDB.code_generation_switch_cases_add_statement("break;")
    transition_block.do(txt, tm)
    LanguageDB.code_generation_switch_cases_add_statement(None)

    txt.append(0)
    txt.append(LanguageDB.INPUT_P_INCREMENT())
    txt.append("\n")

    return txt

def _trivialized_state_machine_coder_do(tm, BeforeGotoReloadAction):
    """This function tries to provide easy solutions for dynamic character
    length encodings, such as UTF8 or UTF16. 
    
    The simplification:

    Check whether all critical checks from inside the 'counter_db' happen in
    the range where there is only one chunk considered (UTF8->1byte at x <
    0x800, UTF16->2byte at x < 0x10000). The range is identified by
    'LowestRangeBorder'. Then implement a simple transition map for this range.
    The remainder of the counter function only implements the input pointer
    increments. They come from a template string given by
    'IncrementActionStr'.

    RETURNS: None -- if no easy solution could be provided.
             text -- the implementation of the counter functionh.
    """
    global __increment_actions_for_utf16
    global __increment_actions_for_utf8
   
    # Currently, we do not handle the case 'Reload': refuse to work.
    if BeforeGotoReloadAction is not None:
        return None

    # (*) Try to find easy and elegant special solutions 
    if   Setup.buffer_codec_transformation_info == "utf8-state-split":
        LowestRangeBorder  = 0x80 
        IncrementActionStr = __increment_actions_for_utf8
    elif Setup.buffer_codec_transformation_info == "utf16-state-split":
        LowestRangeBorder  = 0x10000 
        IncrementActionStr = __increment_actions_for_utf16
    else:
        return None

    # (*) If all but the last interval are exclusively below 0x80, then the 
    #     'easy default utf*' can be applied. 

    # 'last_but_one.end == last.begin', because all intervals are adjacent.
    if tm[-1][0].begin >= LowestRangeBorder: return None

    # The last interval lies beyond the border and has a common action
    # Only add the additional increment instructions.
    tm[-1] = (tm[-1][0], deepcopy(tm[-1][1]))
    tm[-1][1].extend(IncrementActionStr)

    # (*) The first interval may start at - sys.maxint
    if tm[0][0].begin < 0: tm[0][0].begin = 0

    # Later interval shall not!
    assert tm[0][0].end > 0

    # Code the transition map
    return _transition_map_coder_do(tm, BeforeGotoReloadAction=None, UponReloadDoneAdr=None)

def _state_machine_coder_do(tm, BeforeGotoReloadAction):
    """Generates a state machine that represents the transition map 
    according to the codec given in 'Setup.buffer_codec_transformation_info'
    """
    LanguageDB = Setup.language_db

    action_db, sm_list = get_state_machine_list(tm, BeforeGotoReloadAction is not None)

    sm             = get_combined_state_machine(sm_list)
    complete_f, sm = transformation.try_this(sm, -1)
    assert sm is not None

    # The generator only understands 'analyzers'. Get it!
    if BeforeGotoReloadAction is None: engine_type = engine.CHARACTER_COUNTER
    else:                              engine_type = engine.FORWARD

    analyzer = analyzer_generator.do(sm, engine_type)

    sm_txt   = state_machine_coder.do(analyzer, BeforeGotoReloadAction)

    # 'Terminals' are the counter actions
    terminal_txt = LanguageDB["$terminal-code"]("Counter",
                                                action_db, 
                                                VariableDB={},
                                                PreConditionIDList=[],
                                                OnFailureAction=None, 
                                                OnEndOfStreamAction=None, 
                                                OnAfterMatchAction=None, 
                                                Setup=Setup, 
                                                SimpleF=True) 

    txt = sm_txt + terminal_txt
    return txt

def __special(Delta):
    LanguageDB = Setup.language_db
    if Delta != 0: 
        return ["__QUEX_IF_COUNT_COLUMNS_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(Delta)]
    else:
        return []

def __grid_step(GridStepN, ColumnCountPerChunk, IteratorName, ResetReferenceP_F):
    LanguageDB = Setup.language_db
    txt = []
    if ColumnCountPerChunk is not None:
        txt.append(0)
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, IteratorName, ColumnCountPerChunk) 

    txt.append(0)
    txt.extend(LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                    GridStepN, IfMacro="__QUEX_IF_COUNT_COLUMNS"))

    if ColumnCountPerChunk is not None and ResetReferenceP_F:
        txt.append(0)
        LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

    return txt

def __line_n(Delta, ColumnCountPerChunk, IteratorName, ResetReferenceP_F):
    LanguageDB = Setup.language_db
    txt = []
    # Maybe, we only want to set the column counter to '0'.
    # Such action is may be connected to unicode point '0x0D' carriage return.
    if Delta != 0:
        txt.append("__QUEX_IF_COUNT_LINES_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(Delta))
        txt.append(0)
    txt.append("__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n")

    if ColumnCountPerChunk is not None and ResetReferenceP_F:
        txt.append(0)
        LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

    return txt

def __frame(txt, FunctionName, StateMachineF, ColumnCountPerChunk):
    LanguageDB = Setup.language_db

    prologue  =   "#ifdef __QUEX_OPTION_COUNTER\n" \
                + "static void\n" \
                + "%s(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)\n" \
                  % FunctionName \
                + "{\n" \
                + "#   define self (*me)\n" \
                + "    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;\n" 
    if StateMachineF:
       prologue += "    QUEX_TYPE_CHARACTER        input       = (QUEX_TYPE_CHARACTER)0;\n" 
    if ColumnCountPerChunk is not None:
       prologue += "#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)\n"     
       prologue += "    const QUEX_TYPE_CHARACTER* reference_p = LexemeBegin;\n" 
       prologue += "#   endif\n"     

    prologue +=   "\n" \
                + "    __QUEX_IF_COUNT_SHIFT_VALUES();\n" \
                + "\n" \
                + "    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {\n"
    
    LanguageDB.INDENT(txt)
    counter_block = txt
               
    epilogue = []
    if False:
        epilogue.extend([2, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

    epilogue.append("    }\n")
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(epilogue, "iterator", ColumnCountPerChunk) 

    epilogue.append(  "    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */\n" \
                    + "#   undef self\n" \
                    + "}\n" \
                    + "#endif /* __QUEX_OPTION_COUNTER */")

    result = [ prologue ] 
    result.extend(counter_block)
    result.extend(epilogue)

    return "".join(LanguageDB.GET_PLAIN_STRINGS(result))

__increment_actions_for_utf8 = [
     1, "if     ( ((*iterator) & 0x80) == 0 ) { iterator += 1; } /* 1byte character */\n",
     1, "/* NOT ( ((*iterator) & 0x40) == 0 ) { iterator += 2; }    2byte character */\n",
     1, "else if( ((*iterator) & 0x20) == 0 ) { iterator += 2; } /* 2byte character */\n",
     1, "else if( ((*iterator) & 0x10) == 0 ) { iterator += 3; } /* 3byte character */\n",
     1, "else if( ((*iterator) & 0x08) == 0 ) { iterator += 4; } /* 4byte character */\n",
     1, "else if( ((*iterator) & 0x04) == 0 ) { iterator += 5; } /* 5byte character */\n",
     1, "else if( ((*iterator) & 0x02) == 0 ) { iterator += 6; } /* 6byte character */\n",
     1, "else if( ((*iterator) & 0x01) == 0 ) { iterator += 7; } /* 7byte character */\n",
     1, "else                                 { iterator += 1; } /* default 1       */\n",
     1, "continue;\n"
]
    
__increment_actions_for_utf16 = [
     1, "if( *iterator >= 0xD800 && *iterator < 0xE000 ) {\n",
     2, "iterator += 2; continue; /* 2chunk character */\n",
     1, "}\n",
]
    
