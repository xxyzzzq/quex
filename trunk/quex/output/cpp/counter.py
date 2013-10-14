"""____________________________________________________________________________
(C) 2012-2013 Frank-Rene Schaefer
_______________________________________________________________________________
"""
from   quex.engine.generator.base                   import LoopGenerator
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.analyzer.door_id_address_label   import Label

from   quex.blackboard import setup as Setup, \
                              DefaultCounterFunctionDB, \
                              E_MapImplementationType

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
    exit_action          = LoopGenerator.do(counter_db, 
                             IteratorName = "iterator",
                             OnContinue   = [ 1, "continue;" ],
                             OnExit       = None,
                             ReloadF      = False)

    function_name  = "QUEX_NAME(%s_counter)" % Name
    implementation = __frame(function_name, implementation_type, 
                             loop_txt, entry_action, exit_action)

    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

def __frame(FunctionName, ImplementationType, LoopTxt, EntryAction, ExitAction):
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
            "%s:\n" % Label.global_terminal_failure(), 
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
    
    LanguageDB.INDENT(LoopTxt)
               
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
    result.extend(LoopTxt)
    result.extend(epilogue)

    return "".join(LanguageDB.GET_PLAIN_STRINGS(result))

