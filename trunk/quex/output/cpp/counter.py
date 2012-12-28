"""____________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.generator.state.transition.code  import TextTransitionCode
import quex.engine.generator.state.transition.core  as     transition_map_coder
import quex.engine.generator.state_machine_coder    as     state_machine_coder
from   quex.engine.generator.base                   import get_combined_state_machine
from   quex.engine.generator.languages.address      import get_plain_strings
from   quex.engine.generator.action_info            import CodeFragment, \
                                                           PatternActionInfo
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
import quex.engine.analyzer.engine_supply_factory   as     engine
import quex.engine.state_machine.transformation     as     transformation
from   quex.engine.utf8                             import unicode_to_utf8
from   quex.engine.misc.string_handling             import blue_print
from   quex.engine.interval_handling                import NumberSet, Interval

from   quex.blackboard import E_Count, \
                              setup as Setup, \
                              DefaultCounterFunctionDB

from   itertools   import islice
from   collections import defaultdict
from   copy        import deepcopy
import sys
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
    LanguageDB = Setup.language_db

    function_name = DefaultCounterFunctionDB.get_function_name(counter_db)
    if function_name is not None:
        return function_name, None # Implementation has been done before.

    column_counter_per_chunk, state_machine_f, txt = get_step(counter_db, None, None, "iterator")

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(txt, function_name, state_machine_f, column_counter_per_chunk)
    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

Match_input = re.compile("\\binput\\b", re.UNICODE)
def get_step(counter_db, ConcernedActionSet, UndefinedCodePointAction, IteratorName):
    global Match_input

    column_counter_per_chunk, state_machine_f, tm = \
            get_transition_map(counter_db, ConcernedActionSet, UndefinedCodePointAction, IteratorName, 
                               Setup.buffer_codec_transformation_info)

    state_machine_f, txt = get_core_step(tm, IteratorName, state_machine_f)

    return column_counter_per_chunk, state_machine_f, txt

def get_core_step(TM, IteratorName, StateMachineF):
    """Get a counter increment code for one single character.
       RETURNS:
           [0]  -- True, if state machine was implemented.
                -- False, if not.
           [1]  -- source code implementing.
    """
    if StateMachineF:
        txt = _trivialized_state_machine_coder_do(TM)
        if txt is not None:
            StateMachineF = False # We tricked around it; No state machine needed.
        else:
            txt = _state_machine_coder_do(TM)
    else:
        txt = _transition_map_coder_do(TM)

    def replacer(block, StateMachineF):
        if block.find("(me->buffer._input_p)") != -1: 
            block = block.replace("(me->buffer._input_p)", IteratorName)
        if (not StateMachineF) and (Match_input.search(block) is not None): 
            block = block.replace("input", "(*%s)" % IteratorName)
        return block

    for i, elm in enumerate(txt):
        if not isinstance(elm, (str, unicode)): continue
        txt[i] = replacer(elm, StateMachineF)

    return StateMachineF, txt

def get_transition_map(counter_db, ConcernedActionSet=None, 
                       UndefinedCodePointAction=None, IteratorName=None, 
                       Trafo=None): 
    """Implement the core of a counter function by one single transition map.

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

    'AllowReferenceP_F' makes a special kind of optimization available.  In is
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

    The '*' stands for a 'grid' or a 'newline' character. If such a character
    appears, the 'reference_p' is set to the current 'iterator'. As long as
    no such character appears, the term to be added is proportional to
    'iterator - reference_p'. The counter implementation profits from 
    this. It does not increment the 'column_n' as long as only 'normal'
    characters appear. It only adds the delta multiplied with a constant.

    The implementation of this mechanism is implemented by the functions
    '__special()', '__grid()', and '__newline()'. It is controlled there
    by argument 'ColumnCountPerChunk'. If it is not None, it happens to be the 
    factor for the delta addition.
    ___________________________________________________________________________
    RETURNS: [0] not None --> ColumnCountPerChunk, where the specific opti-
                              mazation with the 'reference_p' has been applied.
                 None     --> No optimizatoin with 'reference_p'.

             [1] transition map
    ___________________________________________________________________________
    """
    # If ColumnCountPerChunk is None => no action depends on IteratorName. 
    # See '__special()', '__grid_step()', and '__line_n()'.

    class Builder:
        trafo_info              = None
        concerned_character_set = None
        column_count_per_chunk  = None
        iterator_name           = IteratorName
        factory                 = None
        result                  = []

        @staticmethod
        def do(factory, CharacterSet, Value):
            """Return a list with the intervals of CharacterSet, each interval shall
            be listed together with the 'Entry'.
            """
            if Builder.concerned_character_set is None:
                trigger_set = CharacterSet
            else:
                trigger_set = CharacterSet.intersection(Builder.concerned_character_set)
                if trigger_set.is_empty(): return

            if Builder.trafo_info is not None: 
                trigger_set = trigger_set.clone()
                trigger_set.transform(Builder.trafo_info)

            entry = factory(Value, Builder.iterator_name, Builder.column_count_per_chunk)
            Builder.result.extend((interval, entry) \
                   for interval in trigger_set.get_intervals(PromiseToTreatWellF=True))


    Builder.trafo_info       = Trafo
    state_machine_required_f = False
    if Builder.trafo_info is not None and Setup.variable_character_sizes_f():
        # Block the transformation by setting Builder.trafo_info = None
        Builder.trafo_info       = None
        state_machine_required_f = True

    if UndefinedCodePointAction is not None:
        undefined_code_point_action = UndefinedCodePointAction
    else:
        undefined_code_point_action = \
                    [   "QUEX_ERROR_EXIT(\"Unexpected character for codec '%s'.\\n\"\n" % Setup.buffer_codec, \
                     0, "                \"May be, codec transformation file from unicode contains errors.\");"]

    Builder.concerned_character_set = None
    if ConcernedActionSet is not None:
        Builder.concerned_character_set = NumberSet()
        c_tm = []
        for character_set, action in ConcernedActionSet:
            if Builder.trafo_info is not None:
                character_set = character_set.transform(Builder.trafo_info)
            c_tm.extend((interval, action) for interval in character_set.get_intervals(PromiseToTreatWellF=True))
            Builder.concerned_character_set.unite_with(character_set)
        c_tm.sort()
        transition_map_tool.fill_gaps(c_tm, None)

    # Can column number increment be derived from number of 'chunks'?
    if state_machine_required_f:
        # With variable character sizes we can never, ever derive the 
        # column number increment from the byte-length of a lexeme.
        Builder.column_count_per_chunk = None
    else:
        Builder.column_count_per_chunk = get_column_number_per_chunk(counter_db, Builder.concerned_character_set)

    # Build the 'transition map'
    for delta, character_set in counter_db.special.iteritems():
        Builder.do(__special, character_set, delta)

    for grid_step_n, character_set in counter_db.grid.iteritems():
        Builder.do(__grid_step, character_set, grid_step_n)

    for delta, character_set in counter_db.newline.iteritems():
        Builder.do(__line_n, character_set, delta)

    tm = Builder.result

    transition_map_tool.sort(tm)

    if Builder.concerned_character_set is not None:
        # We need to fill the gaps, to use 'add_transition_actions()'
        transition_map_tool.fill_gaps(tm, undefined_code_point_action)
        tm = transition_map_tool.add_transition_actions(tm, c_tm)

    # The gaps must be places where no characters from unicode are assigned.
    # The original regular expression described unicode. So, the transformation
    # must have done a complete transformation. GAPS must be undefined places.
    transition_map_tool.fill_gaps(tm, undefined_code_point_action)
    transition_map_tool.assert_adjacency(tm)
    if Builder.concerned_character_set is not None:
        tm = transition_map_tool.cut(tm, Builder.concerned_character_set)

    return Builder.column_count_per_chunk, state_machine_required_f, tm

def get_state_machine_list(TM):
    """Returns a state machine list which implements the transition map given
    in unicode. It is assumed that the codec is a variable
    character size codec. Each count action is associated with a separate
    state machine in the list. The association is recorded in 'action_db'.

    RETURNS: [0] -- The 'action_db': state_machine_id --> count action
             [1] -- The list of state machines. 
    """
    LanguageDB = Setup.language_db

    # Sort by actions.
    action_code_db = defaultdict(NumberSet)
    for character_set, action_list in TM:
        action_code_db[tuple(action_list)].unite_with(character_set)

    # Make each action a terminal.
    sm_list   = []
    action_db = {}
    for action, trigger_set in action_code_db.iteritems():
        sm = StateMachine()
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

    RETURNS: None -- If there is no distince column increment 
             > =0 -- The increment of column number for every character
                     from CharacterSet.
    """
    if CharacterSet is None:
        if len(counter_db.special) == 1: return counter_db.special.iterkeys().next()
        else:                            return None

    result = None
    for delta, character_set in counter_db.special.iteritems():
        if character_set.has_intersection(CharacterSet):
            if result is None: result = delta
            else:              return None

    return result

def get_grid_and_line_number_character_set(counter_db):
    result = NumberSet()
    for character_set in counter_db.grid.itervalues():
        result.unite_with(character_set)

    for character_set in counter_db.newline.itervalues():
        result.unite_with(character_set)
    return result

def _transition_map_coder_do(TM):
    
    tm = [ (interval, TextTransitionCode(list(x))) for interval, x in TM ]

    LanguageDB = Setup.language_db
    txt = []
    LanguageDB.code_generation_switch_cases_add_statement("break;")
    transition_map_coder.do(txt, tm, EngineType=engine.CHARACTER_COUNTER)
    LanguageDB.code_generation_switch_cases_add_statement(None)
    txt.append(0)
    txt.append(LanguageDB.INPUT_P_INCREMENT())
    txt.append("\n")

    return txt

def _trivialized_state_machine_coder_do(tm):
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
             text -- the implementation of the counter function.
    """
    global __increment_actions_for_utf16
    global __increment_actions_for_utf8
    LanguageDB = Setup.language_db

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
    return _transition_map_coder_do(tm)

def _state_machine_coder_do(tm):
    """Generates a state machine that represents the transition map 
    according to the codec given in 'Setup.buffer_codec_transformation_info'
    """
    LanguageDB = Setup.language_db

    action_db, sm_list = get_state_machine_list(tm)

    # (Transformation according codec happens inside 'get_combined_state_machine()'
    sm = get_combined_state_machine(sm_list)
    sm = transformation.try_this(sm, -1)
    assert sm is not None

    # The generator only understands 'analyzers'. Get it!
    analyzer = analyzer_generator.do(sm, engine.CHARACTER_COUNTER)

    sm_txt = state_machine_coder.do(analyzer, ReplaceIndentF=False)

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

def __special(Delta, IteratorName, ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    if ColumnCountPerChunk is None and Delta != 0: 
        return ["__QUEX_IF_COUNT_COLUMNS_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(Delta)]
    else:
        return []

def __grid_step(GridStepN, IteratorName, ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    txt = []
    if ColumnCountPerChunk is not None:
        txt.append(0)
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, IteratorName, ColumnCountPerChunk) 

    txt.append(0)
    txt.extend(LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                    GridStepN, IfMacro="__QUEX_IF_COUNT_COLUMNS"))

    if ColumnCountPerChunk is not None:
        txt.append(0)
        LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

    return txt

def __line_n(Delta, IteratorName, ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    txt = []
    # Maybe, we only want to set the column counter to '0'.
    # Such action is may be connected to unicode point '0x0D' carriage return.
    if Delta != 0:
        txt.append("__QUEX_IF_COUNT_LINES_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(Delta))
        txt.append(0)
    txt.append("__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n")

    if ColumnCountPerChunk is not None:
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
        epilog.extend([2, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

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
    
