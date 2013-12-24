"""____________________________________________________________________________
(C) 2012-2013 Frank-Rene Schaefer
_______________________________________________________________________________
"""
import quex.engine.generator.base                   as     generator
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.analyzer.door_id_address_label   import Label, dial_db
from   quex.engine.analyzer.commands                import CommandList, \
                                                           InputPToLexemeStartP, \
                                                           GotoDoorIdIfInputPLexemeEnd

from   quex.blackboard import Lng, \
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

    function_name  = Lng.DEFAULT_COUNTER_FUNCTION_NAME(Name) 

    return_door_id = dial_db.new_door_id()
    code           = generator.do_loop(counter_db, 
                                       AfterExitDoorId = return_door_id,
                                       CheckLexemeEndF = True)

    implementation = __frame(function_name, code, return_door_id) 

    DefaultCounterFunctionDB.enter(counter_db, function_name)

    return function_name, implementation

def __frame(FunctionName, CodeTxt, ReturnDoorId):
    

    txt = [  \
          "#ifdef __QUEX_OPTION_COUNTER\n" \
        + "static void\n" \
        + "%s(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* LexemeBegin, QUEX_TYPE_CHARACTER* LexemeEnd)\n" \
          % FunctionName \
        + "{\n" \
        + "#   define self (*me)\n" \
    ]

    # Following function refers to the global 'variable_db'
    txt.extend(Lng.VARIABLE_DEFINITIONS(variable_db))
    txt.append(
         "    (void)me; (void)LexemeBegin; (void)LexemeEnd;\n"
         "    __QUEX_IF_COUNT_SHIFT_VALUES();\n\n"
       + "    __quex_assert(LexemeBegin <= LexemeEnd);\n"
    )

    txt.extend(CodeTxt)

    txt.append(
         "%s:\n" % dial_db.get_label_by_door_id(ReturnDoorId) \
       + "    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */\n" \
       + "   return;\n" \
       + "#  undef self\n" \
       + "}\n" \
       + "#endif /* __QUEX_OPTION_COUNTER */\n" 
    )

    return "".join(Lng.GET_PLAIN_STRINGS(txt))

