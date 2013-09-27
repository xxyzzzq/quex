from   quex.engine.misc.string_handling        import blue_print
from   quex.engine.analyzer.state.entry_action import DoorID

from   quex.engine.generator.languages.address import Label, \
                                                      map_door_id_to_address, \
                                                      map_door_id_to_label, \
                                                      mark_door_id_as_gotoed, \
                                                      CodeIfDoorIdReferenced, \
                                                      LabelIfDoorIdReferenced
from   quex.engine.interval_handling           import NumberSet
from   quex.blackboard import E_ActionIDs, E_AcceptanceIDs
from   operator import itemgetter
from   copy     import copy
#

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")

#________________________________________________________________________________
# C++
#

__header_definitions_txt = """
#include <quex/code_base/analyzer/member/basic>
#include <quex/code_base/buffer/Buffer>
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue>
#endif

#ifdef    CONTINUE
#   undef CONTINUE
#endif
#define   CONTINUE goto $$GOTO_START_PREPARATION$$; 

#ifdef    RETURN
#   undef RETURN
#endif
"""

__return_with_on_after_match = """
#define RETURN    goto __ON_AFTER_MATCH_THEN_RETURN;
"""
__return_without_on_after_match = """
#define RETURN    __QUEX_PURE_RETURN;
"""

def header_definitions(LanguageDB, OnAfterMatchF):
    assert type(OnAfterMatchF) == bool
    global __return_without_on_after_match
    global __return_with_on_after_match
    assert len(__return_with_on_after_match) > 10
    assert len(__return_without_on_after_match) > 10

    #txt += "/MARK/ %i '%s'\n" % (len(__return_with_on_after_match),    map(ord, __return_with_on_after_match))
    #txt += "/MARK/ '%s'\n" % __return_with_on_after_match
    #txt += "/MARK/ %i '%s'\n" % (len(__return_without_on_after_match), map(ord, __return_without_on_after_match))
    #txt += "/MARK/ '%s'\n" % __return_without_on_after_match
    txt = [ __header_definitions_txt.replace("$$GOTO_START_PREPARATION$$", 
                                             map_door_id_to_label(DoorID.global_reentry_preparation(), GotoedF=True)) ]

    if OnAfterMatchF: txt.append(__return_with_on_after_match)
    else:             txt.append(__return_without_on_after_match)
    return txt

def _local_variable_definitions(VariableDB):
    if len(VariableDB) == 0: return ""

    def __group_by_condition(VariableDB):
        result = {}
        for variable in VariableDB.itervalues():

            variable_list = result.get(variable.condition)
            if variable_list is None: 
                variable_list              = [[], []]
                result[variable.condition] = variable_list

            if not variable.condition_negated_f: variable_list[0].append(variable)
            else:                                variable_list[1].append(variable)

        return result

    def __code(txt, variable):
        variable_type = variable.variable_type
        variable_init = variable.initial_value
        variable_name = variable.name

        if variable.element_n is not None: 
            if variable.element_n != 0:
                variable_name += "[%s]" % repr(variable.element_n)
                if variable_type.find("QUEX_TYPE_GOTO_LABEL") != -1: 
                    variable_name = "(" + variable_name + ")"
            else:
                variable_type += "*"
                variable_init  = ["0x0"]

        if variable_init is None: 
            value = ["/* un-initilized */"]
        else:
            if type(variable_init) != list: variable_init = [ variable_init ]
            value = [" = "] + variable_init

        txt.append("    %s%s %s%s" % \
                   (variable_type, 
                    " " * (30-len(variable_type)), variable_name, 
                    " " * (30 - len(variable_name))))
        txt.extend(value)
        txt.append(";\n")

    # L   = max(map(lambda info: len(info[0]), VariableDB.keys()))
    txt       = []
    for raw_name, variable in sorted(VariableDB.items()):
        if variable.priority_f == False: continue

        if variable.condition is not None:
            if variable.condition_negated_f == False: 
                txt.append("#   ifdef %s\n"  % variable.condition)
            else:
                txt.append("#   ifndef %s\n" %  variable.condition)

        __code(txt, variable)

        if variable.condition is not None:
            txt.append("#   endif /* %s */\n" % variable.condition)

        del VariableDB[variable.name]

    grouped_variable_list = __group_by_condition(VariableDB)
    unconditioned_name_set = set([])
    for condition, groups in sorted(grouped_variable_list.iteritems()):
        if condition is not None: continue
        for variable in groups[0]:
            unconditioned_name_set.add(variable.name)

    for condition, groups in sorted(grouped_variable_list.iteritems()):

        condition_group, negated_condition_group = groups

        if condition is None:
            for variable in condition_group:
                __code(txt, variable)
        else:
            if len(condition_group) != 0:
                txt.append("#   ifdef %s\n"  % condition)

                for variable in condition_group:
                    if variable.name in unconditioned_name_set: continue
                    __code(txt, variable)

            if len(negated_condition_group) != 0:
                if len(condition_group) != 0: txt.append("#   else /* not %s */\n" % condition)
                else:                         txt.append("#   ifndef %s\n"         % condition)

                for variable in negated_condition_group:
                    if variable.name in unconditioned_name_set: continue
                    __code(txt, variable)

            txt.append("#   endif /* %s */\n" % condition)
            
    return txt
         
__function_signature = """
__QUEX_TYPE_ANALYZER_RETURN_VALUE  
QUEX_NAME($$STATE_MACHINE_NAME$$_analyzer_function)(QUEX_TYPE_ANALYZER* me) 
{
    /* NOTE: Different modes correspond to different analyzer functions. The 
     *       analyzer functions are all located inside the main class as static
     *       functions. That means, they are something like 'globals'. They 
     *       receive a pointer to the lexical analyzer, since static members do
     *       not have access to the 'this' pointer.                          */
#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)
    register QUEX_TYPE_TOKEN_ID __self_result_token_id 
           = (QUEX_TYPE_TOKEN_ID)__QUEX_SETTING_TOKEN_ID_UNINITIALIZED;
#   endif
#   ifdef     self
#       undef self
#   endif
#   define self (*((QUEX_TYPE_ANALYZER*)me))
"""

comment_on_post_context_position_init_str = """
    /* Post context positions do not have to be reset or initialized. If a state
     * is reached which is associated with 'end of post context' it is clear what
     * post context is meant. This results from the ways the state machine is 
     * constructed. Post context position's live cycle:
     *
     * (1)   unitialized (don't care)
     * (1.b) on buffer reload it may, or may not be adapted (don't care)
     * (2)   when a post context begin state is passed, then it is **SET** (now: take care)
     * (2.b) on buffer reload it **is adapted**.
     * (3)   when a terminal state of the post context is reached (which can only be reached
     *       for that particular post context), then the post context position is used
     *       to reset the input position.                                              */
"""

def __analyzer_function(StateMachineName, Setup,
                        variable_definitions, function_body, ModeNameList=[]):
    """EngineClassName = name of the structure that contains the engine state.
                         if a mode of a complete quex environment is created, this
                         is the mode name. otherwise, any name can be chosen. 
       SingleModeAnalyzerF = False if a mode for a quex engine is to be created. True
                           if a stand-alone lexical engine is required (without the
                           complete mode-handling framework of quex).
    """              
    LanguageDB          = Setup.language_db
    SingleModeAnalyzerF = Setup.single_mode_analyzer_f

    txt = [
            "#include <quex/code_base/temporary_macros_on>\n",
            __function_signature.replace("$$STATE_MACHINE_NAME$$", StateMachineName),
    ]

    txt.extend(variable_definitions)

    if len(ModeNameList) != 0 and not SingleModeAnalyzerF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt.append("#   define %s%s    (QUEX_NAME(%s))\n" % (name, " " * (L- len(name)), name))

    txt.extend([
        comment_on_post_context_position_init_str,
        "#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \\\n",
        "       || defined(QUEX_OPTION_ASSERTS)\n",
        "    me->DEBUG_analyzer_function_at_entry = me->current_analyzer_function;\n",
        "#   endif\n",
    ])

    txt.append("%s:\n" % Label.global_reentry())

    # -- entry to the actual function body
    txt.append("    %s\n" % LanguageDB.LEXEME_START_SET())
    txt.append("    QUEX_LEXEME_TERMINATING_ZERO_UNDO(&me->buffer);\n")
    
    txt.extend(function_body)

    # -- prevent the warning 'unused variable'
    txt.append( 
        "\n"                                                                                              \
        "    /* Prevent compiler warning 'unused variable': use variables once in a part of the code*/\n" \
        "    /* that is never reached (and deleted by the compiler anyway).*/\n")

    # Mode Names are defined as macros, so the following is not necessary.
    # for mode_name in ModeNameList:
    #    txt.append("    (void)%s;\n" % mode_name)
    txt.append(                                                             \
        "    (void)QUEX_LEXEME_NULL;\n"                                     \
        "    (void)QUEX_NAME_TOKEN(DumpedTokenIdObject);\n"                 \
        "    QUEX_ERROR_EXIT(\"Unreachable code has been reached.\\n\");\n") 

    ## This was once we did not know ... if there was a goto to the initial state or not.
    ## txt += "        goto %s;\n" % label.get(StateMachineName, InitialStateIndex)
    if len(ModeNameList) != 0 and not SingleModeAnalyzerF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt.append("#   undef %s\n" % name)

    txt.append("#   undef self\n")
    txt.append("}\n")

    txt.append("#include <quex/code_base/temporary_macros_off>\n")
    return txt

__terminal_router_str = """
    __quex_debug("terminal router");
    /*  if last_acceptance => goto correspondent acceptance terminal state */
    /*  else               => execute default action                       */
    if( last_acceptance == $$TERMINAL_FAILURE-REF$$ ) {
        goto $$TERMINAL_FAILURE$$; /* TERMINAL: FAILURE */
    }
#   ifdef  QUEX_OPTION_COMPUTED_GOTOS
    goto *last_acceptance;
#   else
    target_state_index = last_acceptance;
    goto $$STATE_ROUTER$$;
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
"""
__terminal_state_prolog  = """
    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */

    /* Lexeme setup: 
     *
     * There is a temporary zero stored at the end of each lexeme, if the action 
     * references to the 'Lexeme'. 'LexemeNull' provides a reference to an empty
     * zero terminated string.                                                    */
#if defined(QUEX_OPTION_ASSERTS)
#   define Lexeme       QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeBegin  QUEX_NAME(access_LexemeBegin)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeL      QUEX_NAME(access_LexemeL)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeEnd    QUEX_NAME(access_LexemeEnd)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#else
#   define Lexeme       (me->buffer._lexeme_start_p)
#   define LexemeBegin  Lexeme
#   define LexemeL      $$LEXEME_LENGTH$$
#   define LexemeEnd    $$INPUT_P$$
#endif

#define LexemeNull      (&QUEX_LEXEME_NULL)
"""

__reentry_preparation_str = """
$$REENTRY_PREPARATION$$:
    /* (*) Common point for **restarting** lexical analysis.
     *     at each time when CONTINUE is called at the end of a pattern.     */
$$ON_AFTER_MATCH$$ 

    /* FAILURE needs not to run through 'on_after_match'. It enters here.    */
$$REENTRY_PREPARATION_2$$:

#   undef Lexeme
#   undef LexemeBegin
#   undef LexemeEnd
#   undef LexemeNull
#   undef LexemeL

#   ifndef __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
#   ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
    if( QUEX_NAME(TokenQueue_is_full)(&self._token_queue) ) {
        return;
    }
#   else
    if( self_token_get_id() != __QUEX_SETTING_TOKEN_ID_UNINITIALIZED) {
        return __self_result_token_id;
    }
#   endif
#   endif
$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$
$$COMMENT_ON_POST_CONTEXT_INITIALIZATION$$
    /*  If a mode change happened, then the function must first return and
     *  indicate that another mode function is to be called. At this point, 
     *  we to force a 'return' on a mode change. 
     *
     *  Pseudo Code: if( previous_mode != current_mode ) {
     *                   return 0;
     *               }
     *
     *  When the analyzer returns, the caller function has to watch if a mode 
     *  change occurred. If not it can call this function again.             */
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    if( me->DEBUG_analyzer_function_at_entry != me->current_analyzer_function ) 
#   endif
    { 
#       if defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        __QUEX_PURE_RETURN;
#       elif defined(QUEX_OPTION_ASSERTS)
        QUEX_ERROR_EXIT("Mode change without immediate return from the lexical analyzer.");
#       endif
    }

    goto $$GOTO_START$$;
"""

def lexeme_macro_definitions(Setup):
    LanguageDB = Setup.language_db
    lexeme_null_object_name = "QUEX_NAME(LexemeNullObject)"
    if Setup.external_lexeme_null_object != "":
        lexeme_null_object_name = Setup.external_lexeme_null_object

    return blue_print(__terminal_state_prolog, [
          ["$$LEXEME_LENGTH$$",      LanguageDB.LEXEME_LENGTH()],
          ["$$INPUT_P$$",            LanguageDB.INPUT_P()],
          ["$$LEXEME_NULL_OBJECT$$", lexeme_null_object_name],
    ])

def __jump_to_backward_input_position_detector_and_return(BIPD_SM, Setup):
    """Pseudo Ambiguous Post Contexts:

       (1) Jump to the BIPD (backward input position detector)
       (2) Provide the jump-back label so that BIPD can jump to it
           once the next input position has been found.

    NOTE: Pseudo-Ambiguous Post Context require that the end of the core 
    pattern is to be searched! One cannot simply restore a position register.
    """
    LanguageDB = Setup.language_db

    bipd_id   = BIPD_SM.get_id()
    door_id   = BIPD_SM.get_action_at_state_machine_entry().door_id
    bipd_str  = "    goto %s; /* Backward input position detector */\n" % \
                map_door_id_to_label(door_id, GotoedF=True)
    # After having finished the analyzis, enter the terminal code, here.
    bipd_str += "%s: /* After return from backward input position detector.\n" % \
                Label.backward_input_position_detector_return(bipd_id)
    ##print "#bipd_str:", bipd_str, bipd_str
    return bipd_str

def __terminal_on_pattern_match(PatternID, Info, SimpleF, Setup):
    """ PatternID     -- ID of the winning pattern.
        Action        -- Action to be performed when pattern wins.
        PatternString -- String that describes the pattern.
    """
    if hasattr(Info, "action") and hasattr(Info, "pattern"):
        action_code    = Info.action().get_code()
        pattern_string = Info.pattern_string()
        bipd_sm        = Info.pattern().bipd_sm
    else:
        action_code    = Info.get_code()
        pattern_string = ""
        bipd_sm        = None

    assert type(action_code) == list

    def safe(Letter):
        if Letter in ['\\', '"', '\n', '\t', '\r', '\a', '\v']: return "\\" + Letter
        else:                                                   return Letter 

    safe_pattern = "".join(safe(x) for x in pattern_string)

    result = []

    # Pseudo-ambiguous post contexts require a backward search of the next
    # input position. If the pattern is not 'pseudo-ambiguous' (which it most
    # likely isn't), then 'user_code_prefix' will be "".
    if bipd_sm is not None:
        result.append(__jump_to_backward_input_position_detector_and_return(bipd_sm, Setup))

    action_code = copy(action_code)
    action_code.insert(0, 0)
    Setup.language_db.INDENT(action_code, 1)
    result.extend(action_code)

    if not SimpleF: 
        result.extend(["\n", 1, "goto %s;\n" % Label.global_reentry_preparation(GotoedF=True)])

    class HelpOut:
        def __init__(self, Code): self.__code = Code
        def get_code(self):       return self.__code
    class HelpOut2:
        def __init__(self, Code): self.__action = HelpOut(Code)
        def action(self):         return self.__action
    
    return __terminally(HelpOut2(result), Label.acceptance(PatternID),
                        Name="%i:   %s" % (PatternID, safe_pattern))

def __terminally(TheAction, TheLabel, Name, Epilog=[]):
    if TheAction is None:
        return []

    txt = [
       "%s: __quex_debug(\"* TERMINAL %s\\n\");\n" % (TheLabel, Name),
        0 
    ]
    txt.extend(TheAction.action().get_code())
    txt.append("\n")
    txt.extend(Epilog)
    return txt

__on_after_match_then_return_str = """
__ON_AFTER_MATCH_THEN_RETURN:
$$ON_AFTER_MATCH$$
#   if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
    return;
#   else
    return __self_result_token_id;
#   endif
"""

def __on_after_match_then_return(OnAfterMatchAction):
    if OnAfterMatchAction is None:
        return "", ""

    on_after_match_str = OnAfterMatchAction.action().get_code_string()
    return_preparation = blue_print(__on_after_match_then_return_str,
                                    [["$$ON_AFTER_MATCH$$",  on_after_match_str]])

    txt = ["__ON_AFTER_MATCH_THEN_RETURN:\n" ]
    txt.append(on_after_match_str)
    txt.append("#   if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)\n" \
               "    return;\n"                                    \
               "#   else\n"                                       \
               "    return __self_result_token_id;\n"             \
               "#   endif\n")

    return return_preparation, on_after_match_str

def reentry_preparation(LanguageDB, PreConditionIDList, OnAfterMatchInfo):
    TerminalFailureRef = "QUEX_LABEL(%i)" % map_door_id_to_address(DoorID.acceptance(E_AcceptanceIDs.FAILURE))
    """Reentry preperation (without returning from the function."""
    # (*) Unset all pre-context flags which may have possibly been set
    if PreConditionIDList is None:
        unset_pre_context_flags_str = ""
    else:
        unset_pre_context_flags_str = "".join([
            "    " + LanguageDB.ASSIGN("pre_context_%s_fulfilled_f" % __nice(pre_context_id), 0)
            for pre_context_id in PreConditionIDList
        ])

    on_after_match_then_return_str, \
    OnAfterMatchStr                 = __on_after_match_then_return(OnAfterMatchInfo)

    txt = on_after_match_then_return_str
    txt += blue_print(__reentry_preparation_str, [
          ["$$REENTRY_PREPARATION$$",                    Label.global_reentry_preparation()],
          ["$$REENTRY_PREPARATION_2$$",                  Label.global_reentry_preparation_2()],
          ["$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$",  unset_pre_context_flags_str],
          ["$$GOTO_START$$",                             Label.global_reentry(GotoedF=True)],
          ["$$ON_AFTER_MATCH$$",                         OnAfterMatchStr],
          ["$$COMMENT_ON_POST_CONTEXT_INITIALIZATION$$", comment_on_post_context_position_init_str],
          ["$$TERMINAL_FAILURE-REF$$",                   TerminalFailureRef],
    ])
    return txt

def terminal_states(TerminalStateDb, PreConditionIDList, Setup, SimpleF=False):
    """NOTE: During backward-lexing, for a pre-context, there is not need for terminal
             states, since only the flag 'pre-context fulfilled is raised.

    """      
    pattern_terminals_code = []

    for pattern_id, state in sorted(TerminalStateDb.iteritems(), key=lambda x: x[0]):
        if pattern_id == E_ActionIDs.ON_END_OF_STREAM:
            txt = __terminally(state.action, Label.global_terminal_end_of_file(),
                Name  = "END_OF_STREAM",
                Epilog=[
                "    /* End of Stream causes a return from the lexical analyzer, so that no\n",
                "     * tokens can be filled after the termination token.                    */\n",
                "    RETURN;\n"
            ])

        elif pattern_id == E_ActionIDs.ON_FAILURE:
            txt = __terminally(state.action, Label.acceptance(E_AcceptanceIDs.FAILURE), 
                               Name = "FAILURE")

        elif pattern_id == E_ActionIDs.ON_AFTER_MATCH:
            continue

        else:
            txt = __terminal_on_pattern_match(pattern_id, state.action, SimpleF, Setup)

        pattern_terminals_code.extend(txt)

    return pattern_terminals_code
    
def __frame_of_all(Code, Setup):
    # namespace_ref   = LanguageDB.NAMESPACE_REFERENCE(Setup.analyzer_name_space)
    # if len(namespace_ref) > 2 and namespace_ref[:2] == "::":  namespace_ref = namespace_ref[2:]
    # if len(namespace_ref) > 2 and namespace_ref[-2:] == "::": namespace_ref = namespace_ref[:-2]
    # "using namespace " + namespace_ref + ";\n"       + \

    implementation_header_str = ""
    if Setup.language == "C":
        implementation_header_str += "#if defined(__QUEX_OPTION_CONVERTER_HELPER)\n"
        implementation_header_str += "#   include \"%s\"\n" % Setup.get_file_reference(Setup.output_buffer_codec_header_i)
        implementation_header_str += "#endif\n"
        implementation_header_str += "#include <quex/code_base/analyzer/headers.i>\n"
        implementation_header_str += "#include <quex/code_base/analyzer/C-adaptions.h>\n"

    lexeme_null_definition = ""
    if Setup.external_lexeme_null_object == "":
        # LexemeNull has been defined elsewhere.
        lexeme_null_definition = "QUEX_TYPE_CHARACTER  QUEX_LEXEME_NULL_IN_ITS_NAMESPACE = (QUEX_TYPE_CHARACTER)0;\n"

    return "".join(["/* #include \"%s\"*/\n" % Setup.get_file_reference(Setup.output_header_file),
                    implementation_header_str,
                    "QUEX_NAMESPACE_MAIN_OPEN\n",
                    lexeme_null_definition,
                    Code,
                    "QUEX_NAMESPACE_MAIN_CLOSE\n"])                     

def __get_if_in_character_set(ValueList):
    assert type(ValueList) == list
    assert len(ValueList) > 0
    txt = "if( "
    for value in ValueList:
        txt += "input == %i || " % value

    txt = txt[:-3] + ") {\n"
    return txt

def __get_if_in_interval(TriggerSet):
    assert TriggerSet.__class__.__name__ == "Interval"
    assert TriggerSet.size() >= 2

    if TriggerSet.size() == 2:
        return "if( input == %i || input == %i ) {\n" % (TriggerSet.begin, TriggerSet.end - 1)
    else:
        return "if( input >= %i && input < %i ) {\n" % (TriggerSet.begin, TriggerSet.end)

def __condition(txt, CharSet):
    first_f = True
    for interval in CharSet.get_intervals(PromiseToTreatWellF=True):
        if first_f: first_f = False
        else:       txt.append(" || ")

        if interval.end - interval.begin == 1:
            txt.append("(C) == 0x%X"                % interval.begin)
        elif interval.end - interval.begin == 2:
            txt.append("(C) == 0x%X || (C) == 0x%X" % (interval.begin, interval.end - 1))
        else:
            txt.append("(C) <= 0x%X && (C) < 0x%X" % (interval.begin, interval.end))

def __indentation_add(Info):
    # (0) If all involved counts are single spaces, the 'counting' can be done
    #     easily by subtracting 'end - begin', no adaption.
    indent_txt = " " * 16
    if Info.homogeneous_spaces():
        return ""

    def __do(txt, CharSet, Operation):
        txt.append(indent_txt + "if( ")
        __condition(txt, CharSet)
        txt.append(" ) { ")
        txt.append(Operation)
        txt.append(" }\\\n")

    txt       = []
    spaces_db = {} # Sort same space counts together
    grid_db   = {} # Sort same grid counts together
    for name, count_parameter in Info.count_db.items():
        count         = count_parameter.get()
        character_set = Info.character_set_db[name].get()
        if count == "bad": continue
        # grid counts are indicated by negative integer for count.
        if count >= 0:
            spaces_db.setdefault(count, NumberSet()).unite_with(character_set)
        else:
            grid_db.setdefault(count, NumberSet()).unite_with(character_set)

    for count, character_set in spaces_db.items():
        __do(txt, character_set, "(I) += %i;" % count)

    for count, character_set in grid_db.items():
        __do(txt, character_set, "(I) += (%i - ((I) %% %i));" % (abs(count), abs(count)))

    return "".join(txt)

def __indentation_check_whitespace(Info):
    all_character_list = map(lambda x: x.get(), Info.character_set_db.values())
    assert len(all_character_list) != 0

    number_set = all_character_list[0]
    for character_set in all_character_list[1:]:
        number_set.unite_with(character_set)

    txt = []
    __condition(txt, number_set)
    return "".join(txt)

def __get_switch_block(VariableName, CaseCodePairList):
    txt = [0, "switch( %s ) {\n" % VariableName]
    next_i = 0
    L = len(CaseCodePairList)
    CaseCodePairList.sort(key=itemgetter(0))
    for case, code in CaseCodePairList: 
        next_i += 1
        txt.append(1)
        case_label = "0x%X" % case
        if next_i != L and CaseCodePairList[next_i][1] == code:
            txt.append("case %s: %s\n" % (case_label, " " * (7 - len(case_label))))
        else:
            txt.append("case %s: %s" % (case_label, " " * (7 - len(case_label))))
            if type(code) == list: txt.extend(code)
            else:                  txt.append(code)
            txt.append("\n")
            
    txt.append(0)
    txt.append("}\n")
    return txt


