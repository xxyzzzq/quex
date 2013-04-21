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
from   quex.engine.generator.languages.address      import get_label
from   quex.engine.state_machine.core               import StateMachine
import quex.engine.analyzer.core                    as     analyzer_generator
import quex.engine.analyzer.transition_map          as     transition_map_tool
from   quex.engine.interval_handling                import NumberSet, Interval
from   quex.engine.tools                            import print_callstack
from   quex.input.files.counter_db                  import CountAction, ExitAction

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
    line and column number counting. 
    
    Multiple modes may have the same character counting behavior. If so, 
    then there's only one counter implemented while others refer to it. 

    ---------------------------------------------------------------------------
    
    RETURNS: function_name, string --> Function name and the implementation 
                                       of the character counter.
             function_name, None   --> The 'None' implementation indicates that
                                       NO NEW counter is implemented. An 
                                       appropriate counter can be accessed 
                                       by the 'function name'.
    ---------------------------------------------------------------------------
    """
    function_name = DefaultCounterFunctionDB.get_function_name(counter_db)
    if function_name is not None:
        return function_name, None # Implementation has been done before.

    implementation_type, \
    loop_txt,            \
    entry_action,        \
    exit_action          = __make_loop(counter_db)

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(implementation_type, loop_txt, 
                             function_name, entry_action, exit_action)

    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

def __make_loop(counter_db):
    # For a counter, there is no 'reload' because the entire lexeme is 
    # inside the buffer.
    IteratorName = "iterator"

    tm,                  \
    implementation_type, \
    entry_action,        \
    exit_action,         \
    dummy,               \
    dummy                = get_counter_map(counter_db, IteratorName) 

    # TODO: The lexer shall never drop-out with exception.
    # 'ON_EXIT' should not occur here
    assert not transition_map_tool.has_action_id(tm, E_ActionIDs.ON_EXIT)
    transition_map_tool.insert_after_action_id(tm, E_ActionIDs.ON_GOOD_TRANSITION,
                                               [ 1, "continue;" ])
    transition_map_tool.assert_no_empty_action(tm)

    implementation_type, \
    loop_txt             = CppGenerator.code_action_map(tm, IteratorName) 

    return implementation_type, loop_txt, entry_action, exit_action

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
    assert ExitCharacterSet is None or not ExitCharacterSet.has_intersection(InsideCharacterSet)

    LanguageDB = Setup.language_db
    # If ColumnCountPerChunk is None => no action depends on IteratorName. 
    # See '__special()', '__grid_step()', and '__line_n()'.

    counter_dictionary = counter_db.get_counter_dictionary(InsideCharacterSet)

    if ColumnCountPerChunk is not None:
        # It *is* conceivable, that there is a subset of 'CharacterSet' which
        # can be handled with a 'column_count_per_chunk' and for all other
        # characters in 'CharacterSet' the user does something to make it fit
        # (see character set skipper, for example).
        column_count_per_chunk = ColumnCountPerChunk
    else:
        column_count_per_chunk = counter_db.get_column_number_per_chunk(InsideCharacterSet)

    cm = []
    for number_set, action in counter_dictionary:
        assert ExitCharacterSet is None or InsideCharacterSet.is_superset(number_set)
        action_txt = action.get_txt(column_count_per_chunk, IteratorName)
        cm.extend((x, action_txt) for x in number_set.get_intervals())

    implementation_type = CppGenerator.determine_implementation_type(cm, ReloadF)

    transition_map_tool.add_action_to_all(cm, CountAction.get_epilog(implementation_type))

    exit_action_txt = ExitAction.get_txt(column_count_per_chunk, IteratorName)
    exit_action_txt.extend(ExitAction.get_epilog(implementation_type))
    if ExitCharacterSet is not None:
        cm.extend((x, exit_action_txt) for x in ExitCharacterSet.get_intervals())

    transition_map_tool.clean_up(cm)

    # Upon reload, the reference pointer may have to be added. When the reload is
    # done the reference pointer needs to be reset. 
    entry_action = []
    exit_action  = []
    if not ReloadF:
        before_reload_action = None
        after_reload_action  = None
        if column_count_per_chunk is not None:
            LanguageDB.REFERENCE_P_COLUMN_ADD(exit_action, IteratorName, column_count_per_chunk)
            LanguageDB.REFERENCE_P_RESET(entry_action, IteratorName, AddOneF=False)
    else:
        before_reload_action = []
        after_reload_action  = []
        if column_count_per_chunk is not None:
            LanguageDB.REFERENCE_P_COLUMN_ADD(before_reload_action, IteratorName, column_count_per_chunk)
            LanguageDB.REFERENCE_P_COLUMN_ADD(exit_action, IteratorName, column_count_per_chunk)
            LanguageDB.REFERENCE_P_RESET(entry_action, IteratorName, AddOneF=False)
            LanguageDB.REFERENCE_P_RESET(after_reload_action, IteratorName, AddOneF=False)

    if column_count_per_chunk is not None:
        variable_db.require("reference_p")

    return cm, implementation_type, entry_action, exit_action, before_reload_action, after_reload_action

def __frame(ImplementationType, CounterTxt, FunctionName, EntryAction, ExitAction):
    LanguageDB = Setup.language_db

    prolog  = [  \
          "#ifdef __QUEX_OPTION_COUNTER\n" \
        + "static void\n" \
        + "%s(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)\n" \
          % FunctionName \
        + "{\n" \
        + "#   define self (*me)\n" \
        + "    QUEX_TYPE_CHARACTER* iterator    = LexemeBegin;\n" 
    ]

    if ImplementationType == E_MapImplementationType.STATE_MACHINE:
        prolog.append("    QUEX_TYPE_CHARACTER  input       = (QUEX_TYPE_CHARACTER)0;\n")
        on_failure_action = [     
            "%s:\n" % get_label("$terminal-FAILURE"), 
            1, "QUEX_ERROR_EXIT(\"State machine failed.\");\n" 
        ]
    else:
        on_failure_action = []


    if variable_db.has_key("reference_p"):
        prolog.append(
             "#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)\n" 
           + "    const QUEX_TYPE_CHARACTER* reference_p = LexemeBegin;\n" 
           + "#   endif\n")

    # There is no 'ExitCharacterSet' in a counter, since a counter works
    # on a pattern which has already matched. It only ends at the LexemeEnd.
    # No character can be half-part parsed. Thus, 'character_begin_p' shall
    # not have been used at this point in time.
    assert not variable_db.has_key("character_begin_p")

    prolog.extend(EntryAction)
    prolog.append(
         "    __QUEX_IF_COUNT_SHIFT_VALUES();\n" \
       + "\n" \
       + "    __quex_assert(LexemeBegin <= LexemeEnd);\n" \
       + "    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {\n")
    
    LanguageDB.INDENT(CounterTxt)
               
    epilogue = []
    epilogue.append("\n    }\n")
    epilogue.append(
        "    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */\n")
    epilogue.extend(ExitAction)
    epilogue.append("   return;\n");
    epilogue.extend(on_failure_action)
    epilogue.append(
         "#  undef self\n" 
       + "}\n"
       + "#endif /* __QUEX_OPTION_COUNTER */"
    )

    # (*) Putting it all together _____________________________________________
    result = prolog
    result.extend(CounterTxt)
    result.extend(epilogue)

    return "".join(LanguageDB.GET_PLAIN_STRINGS(result))

