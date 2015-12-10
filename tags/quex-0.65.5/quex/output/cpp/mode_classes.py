from   quex.engine.misc.string_handling  import blue_print
from   quex.blackboard                   import setup as Setup, \
                                                Lng, \
                                                E_IncidenceIDs
from   operator import attrgetter

def do(ModeDb):
    LexerClassName   = Setup.analyzer_class_name
    DerivedClassName = Setup.analyzer_derived_class_name

    mode_db_setup_txt = __setup(ModeDb)

    # -- mode class member function definitions (on_entry, on_exit, has_base, ...)
    mode_class_member_functions_txt = write_member_functions(ModeDb.values())

    txt  = "".join([
        "QUEX_NAMESPACE_MAIN_OPEN\n",
        mode_db_setup_txt,
        mode_class_member_functions_txt,
        "QUEX_NAMESPACE_MAIN_CLOSE\n"
    ])

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
        if mode.abstract_f(): continue
        txt += get_implementation_of_mode_functions(mode, Modes)

    txt += "#undef self\n"
    txt += "#undef __self_result_token_id\n"
    return txt

mode_function_implementation_str = \
"""
void
QUEX_NAME($$MODE_NAME$$_on_entry)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* FromMode) {
    (void)me;
    (void)FromMode;
$$ENTER-PROCEDURE$$
}

void
QUEX_NAME($$MODE_NAME$$_on_exit)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* ToMode)  {
    (void)me;
    (void)ToMode;
$$EXIT-PROCEDURE$$
}

#if defined(QUEX_OPTION_INDENTATION_TRIGGER) 
void
QUEX_NAME($$MODE_NAME$$_on_indentation)(QUEX_TYPE_ANALYZER*    me, 
                                        QUEX_TYPE_INDENTATION  Indentation, 
                                        QUEX_TYPE_CHARACTER*   Begin) {
    (void)me;
    (void)Indentation;
    (void)Begin;
$$ON_INDENTATION-PROCEDURE$$
}
#endif

#ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
bool
QUEX_NAME($$MODE_NAME$$_has_base)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
$$HAS_BASE_MODE$$
}
bool
QUEX_NAME($$MODE_NAME$$_has_entry_from)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
$$HAS_ENTRANCE_FROM$$
}
bool
QUEX_NAME($$MODE_NAME$$_has_exit_to)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
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
    def __filter_out_abstract_modes(ModeNameList):
        """Return only those names from ModeNameList where the mode is not
        abstract. That is, it can be implemented.
        """
        result = []
        for name in ModeNameList:
            for mode in Modes:
                if mode.name == name:
                    if not mode.abstract_f(): result.append(name)
                    break
        return result

    # (*) on enter 
    on_entry_str  = "#   ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
    on_entry_str += "    QUEX_NAME(%s).has_entry_from(FromMode);\n" % mode.name
    on_entry_str += "#   endif\n"

    code_fragment = mode.incidence_db.get(E_IncidenceIDs.MODE_ENTRY)
    if code_fragment is not None:
        on_entry_str += Lng.SOURCE_REFERENCED(code_fragment)
        if on_entry_str[-1] == "\n": on_entry_str = on_entry_str[:-1]

    # (*) on exit
    on_exit_str  = "#   ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
    on_exit_str += "    QUEX_NAME(%s).has_exit_to(ToMode);\n" % mode.name
    on_exit_str += "#   endif\n"
    code_fragment = mode.incidence_db.get(E_IncidenceIDs.MODE_EXIT)
    if code_fragment is not None:
        on_exit_str += Lng.SOURCE_REFERENCED(code_fragment)

    # (*) on indentation
    on_indentation_str = get_on_indentation_handler(mode)

    # (*) has base mode
    if mode.has_base_mode():
        base_mode_list    = __filter_out_abstract_modes(mode.get_base_mode_name_list())
        has_base_mode_str = get_IsOneOfThoseCode(base_mode_list, CheckBaseModeF=True)
    else:
        has_base_mode_str = "    return false;"
        
    # (*) has entry from
    if mode.entry_mode_name_list is None:
        has_entry_from_str = "    return true; /* default */"        
    else:
        # check whether the mode we come from is an allowed mode
        entry_list         = __filter_out_abstract_modes(mode.entry_mode_name_list)
        has_entry_from_str = get_IsOneOfThoseCode(entry_list,
                                                  ConsiderDerivedClassesF=True)

    # (*) has exit to
    if mode.exit_mode_name_list is None:
        has_exit_to_str = "    return true; /* default */"
    else:
        # By default: one can exit to all modes.
        exit_list       = __filter_out_abstract_modes(mode.exit_mode_name_list)
        has_exit_to_str = get_IsOneOfThoseCode(exit_list,
                                               ConsiderDerivedClassesF=True)
    
    txt = blue_print(mode_function_implementation_str,
                     [
                      ["$$ENTER-PROCEDURE$$",      on_entry_str],
                      ["$$EXIT-PROCEDURE$$",       on_exit_str],
                      #
                      ["$$ON_INDENTATION-PROCEDURE$$", on_indentation_str],
                      #
                      ["$$HAS_BASE_MODE$$",        has_base_mode_str],
                      ["$$HAS_ENTRANCE_FROM$$",    has_entry_from_str],
                      ["$$HAS_EXIT_TO$$",          has_exit_to_str],
                      #
                      ["$$MODE_NAME$$",            mode.name],
                      ])
    return txt

def get_IsOneOfThoseCode(ThoseModes, Indentation="    ",
                         CheckBaseModeF = False,
                         ConsiderDerivedClassesF=False):
    txt = Indentation
    if len(ThoseModes) == 0:
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
            txt += "    if( Mode->has_base(&QUEX_NAME(%s)) ) return true;\n" % mode_name
    else:
        txt += ";\n"
    txt += "}\n"

    txt += "__QUEX_STD_fprintf(stderr, "
    if ConsiderDerivedClassesF or CheckBaseModeF:
        txt += "\"mode '%s' is not one of (and not a derived mode of): " 
    else:
        txt += "\"mode '%s' is not one of: " 
    for mode_name in ThoseModes:
        txt += "%s, " % mode_name
    txt += "\\n\", Mode->name);\n"
    txt += "__quex_assert(false);\n"
    txt += "return false;\n"

    return txt.replace("\n", "\n" + Indentation)

on_indentation_str = """
#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)
#      define __QUEX_RETURN return __self_result_token_id
#   else
#      define __QUEX_RETURN return
#   endif
#   define RETURN    __QUEX_RETURN
#   define CONTINUE  __QUEX_RETURN
#   define Lexeme    LexemeBegin
#   define LexemeEnd (me->buffer._read_p)

    QUEX_NAME(IndentationStack)*  stack = &me->counter._indentation_stack;
    QUEX_TYPE_INDENTATION*        start = 0x0;

    __quex_assert((long)Indentation >= 0);

    if( Indentation > *(stack->back) ) {
        ++(stack->back);
        if( stack->back == stack->memory_end ) QUEX_ERROR_EXIT("Indentation stack overflow.");
        *(stack->back) = Indentation;
$$INDENT-PROCEDURE$$
        __QUEX_RETURN;
    }
    else if( Indentation == *(stack->back) ) {
$$NODENT-PROCEDURE$$
    }
    else  {
        start = stack->back;
        --(stack->back);
#       if ! defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
#       define First true
$$DEDENT-PROCEDURE$$
#       undef  First
#       endif
        while( Indentation < *(stack->back) ) {
            --(stack->back);
#           if ! defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)
#           define First false
$$DEDENT-PROCEDURE$$
#           undef  First
#           endif
        }

        if( Indentation == *(stack->back) ) { 
            /* 'Landing' must happen on indentation border. */
#           define ClosedN (start - stack->back)
$$N-DEDENT-PROCEDURE$$
#           undef  ClosedN
        } else { 
#            define IndentationStackSize ((size_t)(1 + start - stack->front))
#            define IndentationStack(I)  (*(stack->front + I))
#            define IndentationUpper     (*(stack->back))
#            define IndentationLower     ((stack->back == stack->front) ? *(stack->front) : *(stack->back - 1))
#            define ClosedN              (start - stack->back)
$$INDENTATION-ERROR-PROCEDURE$$
#            undef IndentationStackSize 
#            undef IndentationStack  
#            undef IndentationUpper     
#            undef IndentationLower     
#            undef ClosedN
        }
    }
    __QUEX_RETURN;

#   undef Lexeme    
#   undef LexemeEnd 
"""

def get_on_indentation_handler(Mode):
    # 'on_dedent' and 'on_n_dedent cannot be defined at the same time.
    assert not (    E_IncidenceIDs.INDENTATION_DEDENT   in Mode.incidence_db \
                and E_IncidenceIDs.INDENTATION_N_DEDENT in Mode.incidence_db)

    # A mode that deals only with the default indentation handler relies
    # on what is defined in '$QUEX_PATH/analyzer/member/on_indentation.i'
    if Mode.incidence_db.default_indentation_handler_f():
        return "    return;"

    code_fragment = Mode.incidence_db.get(E_IncidenceIDs.INDENTATION_INDENT)
    if code_fragment is not None:
        on_indent_str   = Lng.SOURCE_REFERENCED(code_fragment)
    else:
        on_indent_str   = "self_send(__QUEX_SETTING_TOKEN_ID_INDENT);"

    code_fragment = Mode.incidence_db.get(E_IncidenceIDs.INDENTATION_NODENT)
    if code_fragment is not None:
        on_nodent_str   = Lng.SOURCE_REFERENCED(code_fragment)
    else:
        on_nodent_str   = "self_send(__QUEX_SETTING_TOKEN_ID_NODENT);"

    on_dedent_str   = ""
    on_n_dedent_str = ""
    code_fragment = Mode.incidence_db.get(E_IncidenceIDs.INDENTATION_DEDENT)
    if code_fragment is not None:
        on_dedent_str = Lng.SOURCE_REFERENCED(code_fragment)

    code_fragment = Mode.incidence_db.get(E_IncidenceIDs.INDENTATION_N_DEDENT)
    if code_fragment is not None:
        on_n_dedent_str = Lng.SOURCE_REFERENCED(code_fragment)

    if (not on_dedent_str) and (not on_n_dedent_str):
        # If no 'on_dedent' and no 'on_n_dedent' is defined ... 
        on_dedent_str    = ""
        on_n_dedent_str  = "#if defined(QUEX_OPTION_TOKEN_REPETITION_SUPPORT)\n"
        on_n_dedent_str += "    self_send_n(ClosedN, __QUEX_SETTING_TOKEN_ID_DEDENT);\n"
        on_n_dedent_str += "#else\n"
        on_n_dedent_str += "    while( start-- != stack->back ) self_send(__QUEX_SETTING_TOKEN_ID_DEDENT);\n"
        on_n_dedent_str += "#endif\n"

    code_fragment = Mode.incidence_db.get(E_IncidenceIDs.INDENTATION_ERROR)
    if code_fragment is not None:
        on_indentation_error = Lng.SOURCE_REFERENCED(code_fragment) 
    else:
        # Default: Blow the program if there is an indentation error.
        on_indentation_error = 'QUEX_ERROR_EXIT("Lexical analyzer mode \'%s\': indentation error detected!\\n"' \
                               % Mode.name + \
                               '                "No \'on_indentation_error\' handler has been specified.\\n");'

    # Note: 'on_indentation_bad' is applied in code generation for 
    #       indentation counter in 'indentation_counter.py'.
    txt = blue_print(on_indentation_str,
                     [["$$INDENT-PROCEDURE$$",            on_indent_str],
                      ["$$NODENT-PROCEDURE$$",            on_nodent_str],
                      ["$$DEDENT-PROCEDURE$$",            on_dedent_str],
                      ["$$N-DEDENT-PROCEDURE$$",          on_n_dedent_str],
                      ["$$INDENTATION-ERROR-PROCEDURE$$", on_indentation_error]])
    return txt

def get_related_code_fragments(ModeDb):
    """
       RETURNS:  -- members of the lexical analyzer class for the mode classes
                 -- static member functions declaring the analyzer functions for he mode classes 
                 -- constructor init expressions (before '{'),       
                 -- constructor text to be executed at construction time 
                 -- friend declarations for the mode classes/functions

    """
    Modes = ModeDb.values()
    members_txt = ""    
    for mode in Modes:
        if mode.abstract_f(): continue
        members_txt += "        extern QUEX_NAME(Mode)  QUEX_NAME(%s);\n" % mode.name

    mode_functions_txt = __get_function_declaration(Modes, FriendF=False)
    friends_txt        = __get_function_declaration(Modes, FriendF=True)

    return members_txt,        \
           mode_functions_txt, \
           friends_txt

def __get_function_declaration(Modes, FriendF=False):

    if FriendF: prolog = "    friend "
    else:       prolog = "extern "

    def functions(Prolog, ReturnType, NameList, ArgList):
        txt = ""
        for name in NameList:
            function_signature = "%s QUEX_NAME(%s_%s)(%s);" % \
                     (ReturnType, mode.name, name, ArgList)
            txt += "%s" % Prolog + "    " + function_signature + "\n"

        return txt

    txt = ""
    on_indentation_txt = ""
    for mode in Modes:
        if mode.abstract_f(): continue

        txt += functions(prolog, "__QUEX_TYPE_ANALYZER_RETURN_VALUE", 
                                ["analyzer_function"],
                                "QUEX_TYPE_ANALYZER*")

        # If one of the following events is specified, then we need an 'on_indentation' handler
        if mode.incidence_db.has_key(E_IncidenceIDs.INDENTATION_HANDLER): 
            on_indentation_txt = functions(prolog, "void", ["on_indentation"], 
                                 "QUEX_TYPE_ANALYZER*, QUEX_TYPE_INDENTATION, QUEX_TYPE_CHARACTER*")

        if mode.incidence_db.has_key(E_IncidenceIDs.MODE_ENTRY): 
            txt += functions(prolog, "void", ["on_entry"], 
                                    "QUEX_TYPE_ANALYZER*, const QUEX_NAME(Mode)*")

        if mode.incidence_db.has_key(E_IncidenceIDs.MODE_EXIT): 
            txt += functions(prolog, "void", ["on_exit"], 
                                    "QUEX_TYPE_ANALYZER*, const QUEX_NAME(Mode)*")

        txt += "#ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
        txt += functions(prolog, "bool", ["has_base", "has_entry_from", "has_exit_to"], 
                                "const QUEX_NAME(Mode)*")
        txt += "#endif\n"

    txt += on_indentation_txt
    txt += "\n"

    return txt

def mode_id_definition(ModeDb):
    if not ModeDb: return ""

    result = "".join(
        "    QUEX_NAME(ModeID_%s) = %i,\n" % (mode.name, mode.mode_id)
        for mode in sorted(ModeDb.itervalues(), key=attrgetter("mode_id"))
            if not mode.abstract_f()
    )

    return result[:-2]

def __setup(ModeDb):
    txt = [
        initialization(mode)
        for mode in sorted(ModeDb.itervalues(), key=attrgetter("mode_id")) if not mode.abstract_f()
    ]
    txt.append("\n")
    txt.append("QUEX_NAME(Mode)* (QUEX_NAME(mode_db)[__QUEX_SETTING_MAX_MODE_CLASS_N]) = {\n")

    content_txt = [
        "    &QUEX_NAME(%s),\n" % mode.name
        for mode in sorted(ModeDb.itervalues(), key=attrgetter("mode_id")) if not mode.abstract_f()
    ]
    # delete trailing comma
    if content_txt: 
        content_txt[-1] = "%s\n" % content_txt[-1][:-2]

    txt.extend(content_txt)
    txt.append("};\n")

    return "".join(txt)

def initialization(mode):
    assert not mode.abstract_f()
    
    analyzer_function = "QUEX_NAME(%s_analyzer_function)" % mode.name
    on_indentation    = "QUEX_NAME(%s_on_indentation)"    % mode.name
    on_entry          = "QUEX_NAME(%s_on_entry)"          % mode.name
    on_exit           = "QUEX_NAME(%s_on_exit)"           % mode.name
    has_base          = "QUEX_NAME(%s_has_base)"          % mode.name
    has_entry_from    = "QUEX_NAME(%s_has_entry_from)"    % mode.name
    has_exit_to       = "QUEX_NAME(%s_has_exit_to)"       % mode.name

    #if mode.abstract_f(): 
    #    analyzer_function = "QUEX_NAME(Mode_uncallable_analyzer_function)"

    if not mode.incidence_db.has_key(E_IncidenceIDs.MODE_ENTRY):
        on_entry = "QUEX_NAME(Mode_on_entry_exit_null_function)"

    if not mode.incidence_db.has_key(E_IncidenceIDs.MODE_EXIT):
        on_exit = "QUEX_NAME(Mode_on_entry_exit_null_function)"

    if not mode.incidence_db.has_key(E_IncidenceIDs.INDENTATION_HANDLER):
        on_indentation = "QUEX_NAME(Mode_on_indentation_null_function)"

    txt = blue_print(mode_setup_str,
                [["$$MN$$",             mode.name],
                 ["$analyzer_function", analyzer_function],
                 ["$on_indentation",    on_indentation],
                 ["$on_entry",          on_entry],
                 ["$on_exit",           on_exit],
                 ["$has_base",          has_base],
                 ["$has_entry_from",    has_entry_from],
                 ["$has_exit_to",       has_exit_to]])

    return txt

mode_setup_str = """QUEX_NAME(Mode) QUEX_NAME($$MN$$) = {
    /* id                */ QUEX_NAME(ModeID_$$MN$$),
    /* name              */ "$$MN$$",
#   if      defined(QUEX_OPTION_INDENTATION_TRIGGER) \\
       && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
    /* on_indentation    */ $on_indentation,
#   endif
    /* on_entry          */ $on_entry,
    /* on_exit           */ $on_exit,
#   if      defined(QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK)
    /* has_base          */ $has_base,
    /* has_entry_from    */ $has_entry_from,
    /* has_exit_to       */ $has_exit_to,
#   endif
    /* analyzer_function */ $analyzer_function
};
"""

