from   quex.frs_py.string_handling import blue_print
from   quex.frs_py.file_in         import write_safely_and_close
from   quex.input.setup            import setup as Setup

def do(Modes):
    LexerClassName              = Setup.analyzer_class_name
    TokenClassName              = Setup.token_class_name
    OutputFilestem              = Setup.output_file_stem
    DerivedClassName            = Setup.analyzer_derived_class_name
    DerivedClassHeaderFileName  = Setup.analyzer_derived_class_file

    if DerivedClassHeaderFileName != "": txt = "#include<" + DerivedClassHeaderFileName +">\n"
    else:                                txt = "#include\"" + OutputFilestem +"\"\n"

    txt += "#include <quex/code_base/analyzer/C-adaptions.h>\n"

    # -- mode class member function definitions (on_entry, on_exit, has_base, ...)
    mode_class_member_functions_txt = write_member_functions(Modes.values())

    mode_objects_txt = ""    
    for mode_name, mode in Modes.items():
        if mode.options["inheritable"] == "only": continue
        mode_objects_txt += "/* Global */QUEX_NAME(Mode)  QUEX_NAME(%s);\n" % mode_name

    txt += "QUEX_NAMESPACE_MAIN_OPEN\n"
    txt += mode_objects_txt
    txt += mode_class_member_functions_txt
    txt += "QUEX_NAMESPACE_MAIN_CLOSE\n"

    txt = blue_print(txt, [["$$LEXER_CLASS_NAME$$",         LexerClassName],
                           ["$$LEXER_DERIVED_CLASS_NAME$$", DerivedClassName]])
    
    return txt


def write_member_functions(Modes):

    # -- get the implementation of mode class functions
    #    (on_entry, on_exit, on_indent, on_dedent, has_base, has_entry, has_exit, ...)
    txt  = ""
    txt += "#ifndef __QUEX_INDICATOR_DUMPED_TOKEN_ID_DEFINED\n"
    txt += "    static QUEX_TYPE_TOKEN_ID    QUEX_NAME_TOKEN(DumpedTokenIdObject);\n"
    txt += "#endif\n"
    txt += "#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)\n"
    txt += "#define __self_result_token_id    QUEX_NAME_TOKEN(DumpedTokenIdObject)\n"
    for mode in Modes:        
        if mode.options["inheritable"] == "only": continue
        txt += get_implementation_of_mode_functions(mode, Modes)

    txt += "#undef self\n"
    txt += "#undef __self_result_token_id\n"
    return txt


mode_function_implementation_str = \
"""
    void
    QUEX_NAME($$MODE_NAME$$_on_entry)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* FromMode) {
$$ENTER-PROCEDURE$$
    }

    void
    QUEX_NAME($$MODE_NAME$$_on_exit)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* ToMode)  {
$$EXIT-PROCEDURE$$
    }

#if      defined(__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT) \
    && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
    void
    QUEX_NAME($$MODE_NAME$$_on_indentation)(QUEX_TYPE_ANALYZER*    me, 
                                            QUEX_TYPE_INDENTATION  Indentation, 
                                            QUEX_TYPE_CHARACTER*   Begin) {
#       define Lexeme    Begin
#       define LexemeEnd (me->buffer._input_p)

        QUEX_NAME(IndentationStack)*  stack = &me->counter._indentation_stack;
        QUEX_TYPE_INDENTATION         i     = 0;

        __quex_assert((long)Indentation >= 0);

        if( Indentation > *(stack->back) ) {
            ++(stack->back);
            if( stack->back == me->memory_end ) QUEX_ERROR_EXIT("Indentation stack overflow.");
            *(stack->back) = Indentation;
$$INDENT-PROCEDURE$$
            __QUEX_RETURN;
        }
        else if( Indentation == *(stack->back) ) {
$$NODENT-PROCEDURE$$
        }
        else  {
            while( Indentation < *(stack->back) ) {
                ++i;
                --(stack->back);
            }

#           define ClosedN (i)
$$DEDENT-PROCEDURE$$
#           undef ClosedN

            if( Indentation != *(stack->back) ) { /* 'Landing' must happen on indentation border. */
                self_send(__QUEX_SETTING_TOKEN_ID_INDENTATION_ERROR);
            }
        }
        __QUEX_RETURN;
    }
#endif

#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    bool
    QUEX_NAME($$MODE_NAME$$_has_base)(const QUEX_NAME(Mode)* Mode) {
$$HAS_BASE_MODE$$
    }
    bool
    QUEX_NAME($$MODE_NAME$$_has_entry_from)(const QUEX_NAME(Mode)* Mode) {
$$HAS_ENTRANCE_FROM$$
    }
    bool
    QUEX_NAME($$MODE_NAME$$_has_exit_to)(const QUEX_NAME(Mode)* Mode) {
$$HAS_EXIT_TO$$
    }
#endif    
"""                         

def  get_implementation_of_mode_functions(mode, Modes):
    """Writes constructors and mode transition functions.

                  void quex::lexer::enter_EXAMPLE_MODE() { ... }

       where EXAMPLE_MODE is a lexer mode from the given lexer-modes, and
       'quex::lexer' is the lexical analysis class.
    """
    def __filter_out_inheritable_only(ModeNameList):
        result = []
        for name in ModeNameList:
            for mode in Modes:
                if mode.name == name:
                    if mode.options["inheritable"] != "only": result.append(name)
                    break
        return result

    # (*) on enter 
    on_entry_str  = "#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
    on_entry_str += "__quex_assert(me->%s.has_entry_from(FromMode));\n" % mode.name
    on_entry_str += "#endif\n"
    for code_info in mode.get_code_fragment_list("on_entry"):
        on_entry_str += code_info.get_code()
        if on_entry_str[-1] == "\n": on_entry_str = on_entry_str[:-1]

    # (*) on exit
    on_exit_str  = "#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
    on_exit_str += "__quex_assert(me->%s.has_exit_to(ToMode));\n" % mode.name
    on_exit_str += "#endif\n"
    for code_info in mode.get_code_fragment_list("on_exit"):
        on_exit_str += code_info.get_code()

    # (*) on indentation
    on_indent_str = ""
    for code_info in mode.get_code_fragment_list("on_indent"):
        on_indent_str += code_info.get_code()
        
    on_nodent_str = ""
    for code_info in mode.get_code_fragment_list("on_nodent"):
        on_nodent_str += code_info.get_code()

    on_dedent_str = ""
    for code_info in mode.get_code_fragment_list("on_dedent"):
        on_dedent_str += code_info.get_code()
        
    # (*) has base mode
    if mode.has_base_mode():
        base_mode_list    = __filter_out_inheritable_only(mode.get_base_mode_name_list())
        has_base_mode_str = get_IsOneOfThoseCode(base_mode_list)
    else:
        has_base_mode_str = "    return false;"
        
    # (*) has entry from
    try:
        entry_list         = __filter_out_inheritable_only(mode.options["entry"])
        has_entry_from_str = get_IsOneOfThoseCode(entry_list,
                                                  __filter_out_inheritable_only(ConsiderDerivedClassesF=true))
        # check whether the mode we come from is an allowed mode
    except:
        has_entry_from_str = "    return true; /* default */"        

    # (*) has exit to
    try:
        exit_list       = __filter_out_inheritable_only(mode.options["exit"])
        has_exit_to_str = get_IsOneOfThoseCode(exit_list,
                                               ConsiderDerivedClassesF=true)
    except:
        has_exit_to_str = "    return true; /* default */"

    
    txt = blue_print(mode_function_implementation_str,
                     [["$$ENTER-PROCEDURE$$",      on_entry_str],
                      ["$$EXIT-PROCEDURE$$",       on_exit_str],
                      ["$$INDENT-PROCEDURE$$",     on_indent_str],
                      ["$$NODENT-PROCEDURE$$",     on_nodent_str],
                      ["$$DEDENT-PROCEDURE$$",     on_dedent_str],
                      ["$$HAS_BASE_MODE$$",        has_base_mode_str],
                      ["$$HAS_ENTRANCE_FROM$$",    has_entry_from_str],
                      ["$$HAS_EXIT_TO$$",          has_exit_to_str],
                      ["$$MODE_NAME$$",            mode.name],
                      ])
    return txt

def get_IsOneOfThoseCode(ThoseModes, Indentation="    ",
                         ConsiderDerivedClassesF=False):
    txt = Indentation
    if ThoseModes == []:
        return Indentation + "return false;"
    

    # NOTE: Usually, switch commands do a binary bracketting.
    #       (Cannot be faster here ... is not critical anyway since this is debug code)
    txt  = "\n"
    txt += "switch( Mode->id ) {\n"
    for mode_name in ThoseModes:
        txt += "case QUEX_NAME(ModeID_%s): return true;\n" % mode_name
    txt += "default:\n"
    if ConsiderDerivedClassesF:
        for mode_name in ThoseModes:
            txt += "    if( Mode->has_base(%s) ) return true;\n" % mode_name
    else:
        txt += ";\n"
    txt += "}\n"

    txt += "#ifdef __QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR\n"
    if ConsiderDerivedClassesF:
        txt += "std::cerr << \"mode '%s' is not one of (and not a a derived mode of):\\n\";\n" % mode_name
    else:
        txt += "std::cerr << \"mode '%s' is not one of:\\n\";" % mode_name
    for mode_name in ThoseModes:
            txt += "    std::cerr << \"         %s\\n\";\n" % mode_name
    txt += "#endif\n"
    txt += "return false;\n"

    return txt.replace("\n", "\n" + Indentation)

