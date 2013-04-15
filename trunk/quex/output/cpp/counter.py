"""____________________________________________________________________________
(C) 2012 Frank-Rene Schaefer
_______________________________________________________________________________
"""
import quex.engine.generator.state_machine_coder    as     state_machine_coder
import quex.engine.generator.state.transition.solution  as solution
from   quex.engine.generator.base                   import get_combined_state_machine, \
                                                           Generator as CppGenerator
from   quex.engine.generator.action_info            import CodeFragment
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.state_machine.transformation     as     transformation
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
from   quex.engine.interval_handling                import NumberSet, Interval
from   quex.engine.tools                            import print_callstack

from   quex.blackboard import setup as Setup, \
                              DefaultCounterFunctionDB, \
                              E_StateIndices, \
                              E_ActionIDs, \
                              E_MapImplementationType

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

    # For a counter, there is no 'reload' because the entire lexeme is 
    # inside the buffer.
    IteratorName = "iterator"
    tm,                       \
    implementation_type,      \
    loop_start_label,         \
    entry_action,             \
    dummy,                    \
    dummy                     = get_counter_map(counter_db, IteratorName) 

    # TODO: The lexer shall never drop-out with exception.
    on_failure_action = CodeFragment([     
        "\n", 
        1, "QUEX_ERROR_EXIT(\"State machine failed.\");\n" 
    ])

    implementation_type, \
    txt,                 \
    dummy                = CppGenerator.code_action_map(tm, IteratorName, 
                                                        OnFailureAction = on_failure_action)

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(txt, function_name, implementation_type, loop_start_label, entry_action)
    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

class CountAction:
    __slots__ = ("value")
    def __init__(self, Value):
        self.value = Value

    @staticmethod
    def get_epilog(ImplementationType):
        LanguageDB = Setup.language_db
        result = []
        if ImplementationType != E_MapImplementationType.STATE_MACHINE:
            result.extend([2, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])
        result.append(E_ActionIDs.ON_GOOD_TRANSITION)
        return result

class ExitAction(CountAction):
    def __init__(self):
        CountAction.__init__(self, -1)

    @staticmethod
    def get_txt(ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        result = []
        if ColumnCountPerChunk is not None:
            LanguageDB.REFERENCE_P_COLUMN_ADD(result, IteratorName, ColumnCountPerChunk)
        return result

    @staticmethod
    def get_epilog(ImplementationType):
        LanguageDB = Setup.language_db
        result = []
        if ImplementationType == E_MapImplementationType.STATE_MACHINE:
            # Here, characters are made up of more than one 'chunk'. When the last
            # character needs to be reset, its start position must be known. For 
            # this the 'lexeme start pointer' is used.
            result.extend([1, "%s\n" % LanguageDB.INPUT_P_TO_LEXEME_START()])
        result.append(E_ActionIDs.ON_EXIT)
        return result

class ColumnAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        if ColumnCountPerChunk is None and self.value != 0: 
            return ["__QUEX_IF_COUNT_COLUMNS_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(self.value)]
        else:
            return []

class GridAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        txt = []
        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_COLUMN_ADD(txt, IteratorName, ColumnCountPerChunk) 

        txt.append(0)
        txt.extend(LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                        self.value, IfMacro="__QUEX_IF_COUNT_COLUMNS"))

        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

        return txt


class LineAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        txt        = []
        # Maybe, we only want to set the column counter to '0'.
        # Such action is may be connected to unicode point '0x0D' carriage return.
        if self.value != 0:
            txt.append("__QUEX_IF_COUNT_LINES_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(self.value))
            txt.append(0)
        txt.append("__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n")

        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

        return txt

def get_counter_dictionary(counter_db, ConcernedCharacterSet):
    """Returns a list of NumberSet objects where for each X of the list it holds:

         (i)  X is subset of ConcernedCharacterSet
               
         (ii) It is related to a different counter action than Y,
              for each other object Y in the list.

       RETURNS: 

                    list:    (character_set, count_action)
    """
    def prune(X, ConcernedCharacterSet):
        if ConcernedCharacterSet is None: return X
        else:                             return X.intersection(ConcernedCharacterSet)

    result = []
    for delta, character_set in counter_db.special.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, ColumnAdd(delta)))

    for grid_step_n, character_set in counter_db.grid.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, GridAdd(grid_step_n)))

    for delta, character_set in counter_db.newline.iteritems():
        x = prune(character_set, ConcernedCharacterSet)
        if x.is_empty(): continue
        result.append((x, LineAdd(delta)))

    return result

def get_counter_map(counter_db, 
                    IteratorName          = None,
                    ColumnCountPerChunk   = None,
                    InsideCharacterSet    = None,
                    ExitCharacterSet      = None, 
                    ReloadF               = False):
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
    assert type(ReloadF) == bool
    assert ExitCharacterSet is None or isinstance(ExitCharacterSet, NumberSet)
    assert not ExitCharacterSet.has_intersection(InsideCharacterSet)

    LanguageDB = Setup.language_db
    # If ColumnCountPerChunk is None => no action depends on IteratorName. 
    # See '__special()', '__grid_step()', and '__line_n()'.

    counter_dictionary = get_counter_dictionary(counter_db, InsideCharacterSet)

    if ColumnCountPerChunk is not None:
        # It *is* conceivable, that there is a subset of 'CharacterSet' which
        # can be handled with a 'column_count_per_chunk' and for all other
        # characters in 'CharacterSet' the user does something to make it fit
        # (see character set skipper, for example).
        column_count_per_chunk = ColumnCountPerChunk
    else:
        column_count_per_chunk = get_column_number_per_chunk(counter_db, 
                                                             InsideCharacterSet)

    cm = []
    for number_set, action in counter_dictionary:
        assert InsideCharacterSet.is_superset(number_set)
        action_txt = action.get_txt(column_count_per_chunk, IteratorName)
        cm.extend((x, action_txt) for x in number_set.get_intervals())

    implementation_type = CppGenerator.determine_implementation_type(cm, ReloadF)

    transition_map_tool.add_action_to_all(cm, CountAction.get_epilog(implementation_type))

    exit_action_txt = ExitAction.get_txt(column_count_per_chunk, IteratorName)
    exit_action_txt.extend(ExitAction.get_epilog(implementation_type))
    cm.extend((x, exit_action_txt) for x in ExitCharacterSet.get_intervals())

    transition_map_tool.clean_up(cm)

    # Upon reload, the reference pointer may have to be added. When the reload is
    # done the reference pointer needs to be reset. 
    if not ReloadF:
        before_reload_action = None
        after_reload_action  = None
    else:
        entry_action         = []
        before_reload_action = []
        after_reload_action  = []
        if implementation_type != E_MapImplementationType.STATE_MACHINE:
            after_reload_action.extend([1, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

        if ColumnCountPerChunk is not None:
            LanguageDB.REFERENCE_P_COLUMN_ADD(before_reload_action, IteratorName, ColumnCountPerChunk)
            LanguageDB.REFERENCE_P_RESET(entry_action, IteratorName, AddOneF=False)
            LanguageDB.REFERENCE_P_RESET(after_reload_action, IteratorName, AddOneF=False)
            variable_db.require("reference_p")

    return cm, implementation_type, entry_action, before_reload_action, after_reload_action

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

def __frame(CounterTxt, FunctionName, ImplementationType, EntryAction):
    LanguageDB = Setup.language_db

    prologue  =   \
          "#ifdef __QUEX_OPTION_COUNTER\n" \
        + "static void\n" \
        + "%s(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)\n" \
          % FunctionName \
        + "{\n" \
        + "#   define self (*me)\n" \
        + "    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;\n" 

    input_def = ""
    if ImplementationType == E_MapImplementationType.STATE_MACHINE:
        input_def = "    QUEX_TYPE_CHARACTER        input       = (QUEX_TYPE_CHARACTER)0;\n" 

    reference_p_def = ""
    if variable_db.has_key("reference_p"):
        reference_p_def = \
             "#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)\n" \
           + "    const QUEX_TYPE_CHARACTER* reference_p = LexemeBegin;\n" \
           + "#   endif\n"     


    loop_start = \
         "    __QUEX_IF_COUNT_SHIFT_VALUES();\n" \
       + "\n" \
       + "    __quex_assert(LexemeBegin <= LexemeEnd);\n" \
       + "    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {\n"
    
    LanguageDB.INDENT(CounterTxt)
               
    epilogue = []
    epilogue.append("    }\n")
    epilogue.extend(EntryAction)

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

