"""____________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
_______________________________________________________________________________
"""
import quex.engine.generator.state_machine_coder    as     state_machine_coder
import quex.engine.generator.state.transition.solution  as solution
from   quex.engine.generator.base                   import get_combined_state_machine, \
                                                           Generator as CppGenerator
from   quex.engine.generator.action_info            import CodeFragment
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
from   quex.engine.interval_handling                import NumberSet, Interval
from   quex.engine.tools                            import print_callstack

from   quex.blackboard import setup as Setup, \
                              DefaultCounterFunctionDB, \
                              E_StateIndices

from   collections import defaultdict
from   copy        import deepcopy, copy

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

    IteratorName = "iterator"
    tm, column_counter_per_chunk = get_counter_map(counter_db, IteratorName, 
                                                   ActionEpilog=["continue;\n"]) 

    # TODO: The lexer shall never drop-out with exception.
    on_failure_action = CodeFragment([     
        "\n", 
        1, "QUEX_ERROR_EXIT(\"State machine failed.\");\n" 
    ])

    state_machine_f, \
    txt,             \
    dummy            = CppGenerator.code_action_map(tm, IteratorName, 
                                                    OnFailureAction = on_failure_action)

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(txt, function_name, state_machine_f, column_counter_per_chunk)
    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

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
                    ColumnCountPerChunk      = None,
                    ConcernedCharacterSet    = None,
                    DoNotResetReferenceP_Set = None, 
                    ActionEpilog             = []):
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

    if False and Setup.variable_character_sizes_f():
        done_set = set() # 'Actions' may occur on multiple intervals
        for interval, action in cm:
            if id(action) in done_set: continue
            done_set.add(id(action))
            action.append(0)
            action.extend(ActionEpilog)

    return cm, column_count_per_chunk

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

def __frame(CounterTxt, FunctionName, StateMachineF, ColumnCountPerChunk):
    LanguageDB = Setup.language_db

    prologue  =   \
          "#ifdef __QUEX_OPTION_COUNTER\n" \
        + "static void\n" \
        + "%s(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)\n" \
          % FunctionName \
        + "{\n" \
        + "#   define self (*me)\n" \
        + "    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;\n" 

    if StateMachineF:
        input_def = "    QUEX_TYPE_CHARACTER        input       = (QUEX_TYPE_CHARACTER)0;\n" 
    else:
        input_def = ""

    if ColumnCountPerChunk is not None:
        reference_p_def = \
             "#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)\n" \
           + "    const QUEX_TYPE_CHARACTER* reference_p = LexemeBegin;\n" \
           + "#   endif\n"     
    else:
        reference_p_def = ""


    loop_start = \
         "    __QUEX_IF_COUNT_SHIFT_VALUES();\n" \
       + "\n" \
       + "    __quex_assert(LexemeBegin <= LexemeEnd);\n" \
       + "    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {\n"
    
    LanguageDB.INDENT(CounterTxt)
               
    epilogue = []
    epilogue.append("    }\n")
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(epilogue, "iterator", ColumnCountPerChunk) 

    epilogue.append(
         "    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */\n" \
       + "#   undef self\n" \
       + "}\n" \
       + "#endif /* __QUEX_OPTION_COUNTER */")

    result = [ 
         prologue,
         input_def,
         reference_p_def,
         loop_start
    ] 
    result.extend(CounterTxt)
    result.extend(epilogue)

    return "".join(LanguageDB.GET_PLAIN_STRINGS(result))

