from quex.frs_py.file_in         import is_identifier_start, is_identifier_continue
from quex.frs_py.string_handling import blue_print

import quex.core_engine.state_machine.index as index
from quex.core_engine.generator.languages.address import *
from quex.core_engine.interval_handling   import NumberSet
from copy     import copy
from operator import itemgetter
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
#define   CONTINUE $$GOTO_START_PREPARATION$$ 

#ifdef    RETURN
#   undef RETURN
#endif

#if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
#   define RETURN   return
#else
#   define RETURN   do { return __self_result_token_id; } while(0)
#endif
"""

def __header_definitions(LanguageDB):

    txt = __header_definitions_txt
    txt = txt.replace("$$GOTO_START_PREPARATION$$", LanguageDB["$goto"]("$re-start"))
    return txt

def __local_variable_definitions(VariableDB):
    if len(VariableDB) == 0: return ""

    def __interpret(RawName):
        if RawName.find("/") == -1: return "", False, RawName

        # variable name: CONDITION "/" VARIABLE NAME
        # CONDITION builds an 'ifdef' or 'ifndef' region.
        # CONDITION starting with '!' means 'not', thus '! X/a'
        #           is only defined if X is undefined
        fields = RawName.split("/")
        assert len(fields) == 2
        name = fields[1].strip()
        if fields[0][0] == "!": condition_negated_f = True;  condition = fields[0][1:].strip()
        else:                   condition_negated_f = False; condition = fields[0].strip()
        return condition, condition_negated_f, name

    def __group_by_condition(VariableDB):
        result = {}
        for name, info in VariableDB.iteritems():
            condition, condition_negated_f, name = __interpret(name)

            variable_list = result.get(condition)
            if variable_list == None: 
                variable_list     = [[], []]
                result[condition] = variable_list
            if not condition_negated_f:
                variable_list[0].append((name, info))
            else:
                variable_list[1].append((name, info))

        return result

    def __code(txt, name, info):
        type = info[0]
        if len(info) > 2 and info[2] != None: 
            if info[2] != 0:
                name  += "[%s]" % repr(info[2])
                if type.find("QUEX_TYPE_GOTO_LABEL"): name = "(" + name + ")"
                if info[1] != None: value = " = " + info[1]
                else:               value = "/* un-initilized */"
            else:
                type  += "*"
                value  = " = 0x0"
        else:
            value = " = " + info[1]

        txt.append("    %s%s %s%s%s;\n" % (type, " " * (30-len(type)), name, " " * (30 - len(name)), value))

    # L   = max(map(lambda info: len(info[0]), VariableDB.keys()))
    txt = []
    # Some variables need to be defined before others, use 'First' to indicate that
    done_list = []
    for raw_name, info in sorted(VariableDB.items()):
        if "First" not in info: continue

        condition, condition_negated_f, name = __interpret(raw_name)

        if condition != "":
            if condition_negated_f == False: txt.append("#   ifdef %s\n"  % condition)
            else:                            txt.append("#   ifndef %s\n" %  condition)

        __code(txt, name, info)

        if condition != "":
            txt.append("#   endif /* %s */\n" % condition)

        del VariableDB[name]

    grouped_variable_list = __group_by_condition(VariableDB)
    unconditioned_name_set = set([])
    for condition, groups in sorted(grouped_variable_list.iteritems()):
        if condition != "": continue
        condition_group, dummy = groups
        for name, info in condition_group:
            unconditioned_name_set.add(name)

    for condition, groups in sorted(grouped_variable_list.iteritems()):

        condition_group, negated_condition_group = groups
        if condition != "":
            if len(condition_group) != 0:
                txt.append("#   ifdef %s\n"  % condition)

                for name, info in condition_group:
                    if name in unconditioned_name_set: continue
                    __code(txt, name, info)

            if len(negated_condition_group) != 0:
                if len(condition_group) != 0: txt.append("#   else /* not %s */\n" % condition)
                else:                         txt.append("#   ifndef %s\n" % condition)

                for name, info in negated_condition_group:
                    if name in unconditioned_name_set: continue
                    __code(txt, name, info)

            txt.append("#   endif /* %s */\n" % condition)
        else:
            for name, info in condition_group:
                __code(txt, name, info)
            
    return "".join(txt)
         
__function_signature = """
__QUEX_TYPE_ANALYZER_RETURN_VALUE  
QUEX_NAME($$STATE_MACHINE_NAME$$_analyzer_function)(QUEX_TYPE_ANALYZER* me) 
{
    /* NOTE: Different modes correspond to different analyzer functions. The analyzer  
             functions are all located inside the main class as static functions. That  
             means, they are something like 'globals'. They receive a pointer to the   
             lexical analyzer, since static member do not have access to the 'this' pointer.
     */
#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)
    register QUEX_TYPE_TOKEN_ID __self_result_token_id 
           = (QUEX_TYPE_TOKEN_ID)__QUEX_SETTING_TOKEN_ID_UNINITIALIZED;
#   endif
#   ifdef     self
#       undef self
#   endif
#   define self (*((QUEX_TYPE_ANALYZER*)me))
"""

reload_forward_str = """
__RELOAD_FORWARD:
    __quex_debug("__RELOAD_FORWARD");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);

__RELOAD_INIT_STATE:
    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        goto _$$INIT_STATE$$; /* Init state entry */
    }
    goto $$END_OF_STREAM$$;  /* End of stream    */
"""

reload_backward_str = """
__RELOAD_BACKWARD:
    __quex_debug("__RELOAD_BACKWARD");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( QUEX_NAME(Buffer_is_begin_of_file)(&me->buffer) == false ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_backward)(&me->buffer);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);
"""

comment_on_post_context_position_init_str = """
    /* Post context positions do not have to be reset or initialized. If a state
     * is reached which is associated with 'end of post context' it is clear what
     * post context is meant. This results from the ways the state machine is 
     * constructed. A post context positions live time looks like the following:
     *
     * (1)   unitialized (don't care)
     * (1.b) on buffer reload it may, or may not be adapted (don't care)
     * (2)   when a post context begin state is passed, the it is **SET** (now: take care)
     * (2.b) on buffer reload it **is adapted**.
     * (3)   when a terminal state of the post context is reached (which can only be reached
     *       for that particular post context, then the post context position is used
     *       to reset the input position.                                              */
"""


def __analyzer_function(StateMachineName, EngineClassName, StandAloneEngineF,
                        function_body, PostConditionedStateMachineID_List, PreConditionIDList,
                        ModeNameList=[], InitialStateIndex=-1, LanguageDB=None,
                        LocalVariableDB={}):   
    """EngineClassName = name of the structure that contains the engine state.
                         if a mode of a complete quex environment is created, this
                         is the mode name. otherwise, any name can be chosen. 
       StandAloneEngineF = False if a mode for a quex engine is to be created. True
                           if a stand-alone lexical engine is required (without the
                           complete mode-handling framework of quex).
        
       NOTE: If a stand-alone lexer is requested, then there are two functions that are
             created additionally: 

               'EngineClassName'_init(EngineClassName* me,
                                      QUEX_TYPE_CHARACTER StartInputPosition);

                     This function has to be called before starting the lexing process.
                     See the unit tests for examples.
               
               'EngineClassName'_do(EngineClassName* me);
                     
                     This function does a lexical analysis from the current position as
                     it is stored in 'me'.
    """              
    txt = ""

    signature = __function_signature

    txt  = "#include <quex/code_base/temporary_macros_on>\n"
    txt += signature
    txt  = txt.replace("$$STATE_MACHINE_NAME$$", StateMachineName) 

    txt += "    " + LanguageDB["$comment"]("me = pointer to state of the lexical analyzer") + "\n"

    PostContextN = len(PostConditionedStateMachineID_List)

    local_variable_list = LocalVariableDB
    local_variable_list.update(
        { "last_acceptance":                ["QUEX_TYPE_GOTO_LABEL",         "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")],
          "last_acceptance_input_position": ["QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER*)(0x00)"],
          "post_context_start_position":    ["QUEX_TYPE_CHARACTER_POSITION", None, PostContextN],
          "PostContextStartPositionN":      ["const size_t",                 "(size_t)" + repr(PostContextN)],
          "input":                          ["QUEX_TYPE_CHARACTER",          "(QUEX_TYPE_CHARACTER)(0x00)"],
          "target_state_else_index":        ["QUEX_TYPE_GOTO_LABEL",         "(QUEX_TYPE_CHARACTER)(0x00)"],
          "target_state_index":             ["QUEX_TYPE_GOTO_LABEL",         "(QUEX_TYPE_CHARACTER)(0x00)"],
         })
              
    # -- pre-condition fulfillment flags                
    for pre_context_sm_id in PreConditionIDList:
        local_variable_list["pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id)] = ["int", "0"]

    if not StandAloneEngineF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt += "#   define %s%s    (QUEX_NAME(%s))\n" % (name, " " * (L- len(name)), name) 

    txt += LanguageDB["$local-variable-defs"](local_variable_list)
    txt += comment_on_post_context_position_init_str
    txt += "#if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \\\n"
    txt += "    || defined(QUEX_OPTION_ASSERTS)\n"
    txt += "    me->DEBUG_analyzer_function_at_entry = me->current_analyzer_function;\n"
    txt += "#endif\n"

    txt += LanguageDB["$label-def"]("$start")
    txt += "\n"

    # -- entry to the actual function body
    txt += "    " + LanguageDB["$mark-lexeme-start"] + "\n"
    txt += "    if( me->buffer._character_at_lexeme_start != (QUEX_TYPE_CHARACTER)'\\0' ) {\n"  
    txt += "        *(me->buffer._input_p) = me->buffer._character_at_lexeme_start;\n"                  
    txt += "        me->buffer._character_at_lexeme_start = (QUEX_TYPE_CHARACTER)'\\0';\n"
    txt += "    }\n"
    
    txt += function_body

    # -- prevent the warning 'unused variable'
    txt += "\n"
    txt += "    /* Prevent compiler warning 'unused variable': use variables once in a part of the code*/\n"
    txt += "    /* that is never reached (and deleted by the compiler anyway).*/\n"
    for mode_name in ModeNameList:
        txt += "    (void)%s;\n" % mode_name
    txt += "    (void)QUEX_NAME(LexemeNullObject);\n"
    txt += "    (void)QUEX_NAME_TOKEN(DumpedTokenIdObject);\n"
    txt += "    QUEX_ERROR_EXIT(\"Unreachable code has been reached.\\n\");\n"
    txt += "    /* In some scenarios, the __TERMINAL_ROUTER is never required.\n"
    txt += "     * Still, avoid the warning of 'label never used'.             */\n"
    txt += "    goto __TERMINAL_ROUTER;\n"

    txt += blue_print(reload_forward_str,
                      [
                          ["$$INIT_STATE$$",    __nice(InitialStateIndex)],
                          ["$$END_OF_STREAM$$", label_db_get("$terminal-EOF", GotoTargetF=True)],
                      ])

    if len(PreConditionIDList) != 0: 
        txt += reload_backward_str

    ## This was once we did not know ... if there was a goto to the initial state or not.
    ## txt += "        goto %s;\n" % label.get(StateMachineName, InitialStateIndex)

    if not StandAloneEngineF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt += "#   undef %s\n" % name 

    txt += "#undef self\n"
    txt += "}\n"

    # -- the name of the game
    txt = txt.replace("$$QUEX_ANALYZER_STRUCT_NAME$$", EngineClassName)

    txt += "#include <quex/code_base/temporary_macros_off>\n"
    return txt

__terminal_state_str  = """
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
#   define LexemeBegin  QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeL      QUEX_NAME(access_LexemeL)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeEnd    QUEX_NAME(access_LexemeEnd)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#else
#   define Lexeme       (me->buffer._lexeme_start_p)
#   define LexemeBegin  (me->buffer._lexeme_start_p)
#   define LexemeL      ((size_t)(me->buffer._input_p - me->buffer._lexeme_start_p))
#   define LexemeEnd    (me->buffer._input_p)
#endif

#define LexemeNull   (&QUEX_NAME(LexemeNullObject))

$$SPECIFIC_TERMINAL_STATES$$

$$TERMINAL_END_OF_STREAM-DEF$$
$$END_OF_STREAM_ACTION$$
     /* End of Stream causes a return from the lexical analyzer, so that no
      * tokens can be filled after the termination token.                    */
     RETURN;          

$$TERMINAL_FAILURE-DEF$$ /* TERMINAL: FAILURE */
$$FAILURE_ACTION$$
     $$GOTO_START_PREPARATION$$

#undef Lexeme
#undef LexemeBegin
#undef LexemeEnd
#undef LexemeNull
#undef LexemeL
"""

__terminal_router_str = """
    __quex_assert_no_passage(); 
__TERMINAL_ROUTER: 
    __quex_debug("terminal router");
    /*  if last_acceptance => goto correspondent acceptance terminal state */
    /*  else               => execute defaul action                        */
    if( last_acceptance == $$TERMINAL_FAILURE-REF$$ ) {
        goto $$TERMINAL_FAILURE$$; /* TERMINAL: FAILURE */
    }
    /* When a terminal router is used, the terminal is determined dynamically,
     * thus the last_acceptance_input_position **must** be set. 
     * Exception: Template States, where acceptance states of post conditions
     *            do not set the acceptance position (because its retrieved
     *            anyway from post_context_start_position[i]).               */
    if(last_acceptance_input_position != 0x0) {
        $$RESTORE_LAST_ACCEPTANCE_POS$$
    }
#   ifdef  QUEX_OPTION_COMPUTED_GOTOS
    goto *last_acceptance;
#   else
    /* Route according variable 'last_acceptance'. */
    switch( last_acceptance ) {
$$JUMPS_TO_ACCEPTANCE_STATE$$
        default: QUEX_ERROR_EXIT("Terminal router: unknown index.");
    }
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
"""

__on_continue_reentry_preparation_str = """
  
$$REENTRY_PREPARATION$$
    /* (*) Common point for **restarting** lexical analysis.
     *     at each time when CONTINUE is called at the end of a pattern. */
    
#   ifndef __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
#   ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
    if( QUEX_NAME(TokenQueue_is_full)(&self._token_queue) ) RETURN;
#   else
    if( self_token_get_id() != __QUEX_SETTING_TOKEN_ID_UNINITIALIZED) RETURN;
#   endif
#   endif

    last_acceptance = $$TERMINAL_FAILURE-REF$$; /* TERMINAL: FAILURE */
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
     *  When the analyzer returns, the caller function has to watch if a mode change
     *  occured. If not it can call this function again.                               */
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    if( me->DEBUG_analyzer_function_at_entry != me->current_analyzer_function ) 
#   endif
    { 
#       if defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        RETURN;
#       elif defined(QUEX_OPTION_ASSERTS)
        QUEX_ERROR_EXIT("Mode change without immediate return from the lexical analyzer.");
#       endif
    }

    $$GOTO_START$$
"""

def __adorn_action_code(action_info, SMD, SupportBeginOfLineF, IndentationOffset=4): 

    result = action_info.action().get_code()
    if type(result) != tuple: 
        code_str    = result
        variable_db = {}
    else:
        code_str    = result[0]
        variable_db = result[1]

    if code_str == "": return "", variable_db

    indentation = " " * IndentationOffset 
    txt = "\n"
    # TODO: There could be a differenciation between a pattern that contains
    #       newline at the end, and those that do not. Then, there need not
    #       be a conditional question.
    if SupportBeginOfLineF:
        txt += indentation + "me->buffer._character_before_lexeme_start = *(me->buffer._input_p - 1);\n"

    if action_info.action().require_terminating_zero_f():
        txt += indentation + "QUEX_NAME(Buffer_set_terminating_zero_for_lexeme)(&me->buffer);\n"

    # txt += indentation + "{\n"
    txt += code_str.replace("\n", "\n    ") + "\n"  
    # txt += indentation + "}\n"

    return txt, variable_db

def get_terminal_code(state_machine_id, SMD, pattern_action_info, SupportBeginOfLineF, LanguageDB):
    state_machine                  = SMD.sm()
    DirectlyReachedTerminalID_List = SMD.directly_reached_terminal_id_list()

    txt         = ""
    variable_db = {}

    state_machine_id_str = __nice(state_machine_id)
    state_machine        = pattern_action_info.pattern_state_machine()
    #
    action_code, db = __adorn_action_code(pattern_action_info, SMD, SupportBeginOfLineF)
    variable_db.update(db)
        
    # (*) The 'normal' terminal state can also be reached by the terminal
    #     router and, thus, **must** restore the acceptance input position. This is so, 
    #     because when the 'goto last_acceptance' is triggered the 'last_acceptance'
    #     may lay backwards and needs to be restored.
    safe_pattern = pattern_action_info.pattern.replace('"', 'double-quote')
    safe_pattern = safe_pattern.replace("\\n", "\\\\n")
    safe_pattern = safe_pattern.replace("\\t", "\\\\t")
    safe_pattern = safe_pattern.replace("\\r", "\\\\r")
    safe_pattern = safe_pattern.replace("\\a", "\\\\a")
    safe_pattern = safe_pattern.replace("\\v", "\\\\v")
    txt += LanguageDB["$label-def"]("$terminal", state_machine_id) + "\n"
    txt += "    __quex_debug(\"pre-terminal %i: %s\");\n" % (state_machine_id, safe_pattern)
    txt += "    " + LanguageDB["$input/increment"] + "\n"

    txt += LanguageDB["$label-def"]("$terminal-direct", state_machine_id) + "\n"
    txt += "    __quex_debug(\"* terminal %i:   %s\");" % (state_machine_id, safe_pattern)

    # (1) Retrieving the input position for the next run
    #     -- Terminal states can be reached directly, so that the input position
    #        is already set correctly, or via the terminal router because the
    #        acceptance was 'trailing'. Example two patterns A:'for' and B:'forest'.
    #        If the input is 'for' than the pattern A triggers acceptance, but
    #        the lexer still continue trying for B. If the input is 'fortune', 
    #        then the input position must be after 'for' because B was not matched.
    #        The right terminal is reached via the terminal router, and the
    #        terminal router also resets the input position to 'last_acceptance_position'.
    if state_machine.core().post_context_backward_input_position_detector_sm() != None:
        # Pseudo Ambiguous Post Contexts:
        # -- require that the end of the core pattern is to be searched! One 
        #    cannot simply restore some stored input position.
        # -- The pseudo-ambiguous post condition is translated into a 'normal'
        #    pattern. However, after a match a backward detection of the end
        #    of the core pattern is done. Here, we first need to go to the point
        #    where the 'normal' pattern ended, then we can do a backward detection.
        txt += "    PAPC_input_postion_backward_detector_%s(me);\n" % \
               __nice(state_machine.core().post_context_backward_input_position_detector_sm_id())

    elif state_machine.core().post_context_id() != -1L: 
        post_condition_index = SMD.get_post_context_index(state_machine_id)
        # Post Contexted Patterns:
        # -- have a dedicated register from where they store the end of the core pattern.
        variable = "post_context_start_position[%s]" % __nice(post_condition_index) 
        txt += "    " + LanguageDB["$comment"]("post context index '%s' == state machine '%s'" % \
                                               (__nice(post_condition_index), __nice(state_machine_id))) + "\n"
        txt += "    " + LanguageDB["$input/seek_position"](variable) + "\n"

    else:
        # Normal Acceptance:
        pass

    # -- paste the action code that correponds to the pattern   
    txt += action_code + "\n"    
    txt += "    " + LanguageDB["$goto"]("$re-start") + "\n" 
    txt += "\n"

    return txt, variable_db

def __terminal_states(SMD, action_db, OnFailureAction, EndOfStreamAction, 
                      SupportBeginOfLineF, PreConditionIDList, LanguageDB):
    """NOTE: During backward-lexing, for a pre-condition, there is not need for terminal
             states, since only the flag 'pre-condition fulfilled is raised.
    """      
    assert SMD.__class__.__name__ == "StateMachineDecorator"
    sm = SMD.sm()
    PostConditionedStateMachineID_List = SMD.post_contexted_sm_id_list()
    DirectlyReachedTerminalID_List     = SMD.directly_reached_terminal_id_list()

    # (*) specific terminal states of patterns (entered from acceptance states)
    txt = ""
    variable_db = {}
    for state_machine_id, pattern_action_info in action_db.items():
        code, db = get_terminal_code(state_machine_id, SMD, pattern_action_info, SupportBeginOfLineF, LanguageDB)
        txt += code
        variable_db.update(db)
    specific_terminal_states_str = txt

    # (*) general terminal state (entered from non-acceptance state)    
    # terminal_state_idx_list = sorted(action_db.keys())
    # lowest_terminal_id      = terminal_state_idx_list[0]
    # def binary_bracket(IdxList):
    #     L = len(IdxList)
    #     Middle = L / 2
    #     if L > 1: 
    #         return "    " + "if( last_acceptance < %i ) {\n" % Middle + \
    #                "    " +     binary_bracket(IdxList[:Middle]) + \
    #                "    " + "} else {\n" + \
    #                "    " +     binary_bracket(IdxList[Middle:]) + \
    #                "    " + "}\n"
    #     else:
    #         if IdxList[0] == lowest_terminal_id:
    #             return "    " + LanguageDB["$goto"]("$terminal-FAILURE")]
    #         else:
    #             return "    " + "goto TERMINAL_%i;\n" % IdxList[0]
    # jumps_to_acceptance_states_str = binary_bracket(terminal_state_idx_list)
                          
    txt = ""    
    for state_machine_id in action_db.keys():
        label_id = get_address("$terminal-direct", state_machine_id)
        txt += "        case %i: " % label_id
        txt += LanguageDB["$goto"]("$terminal-direct", state_machine_id) + "\n"
    jumps_to_acceptance_states_str = txt

    # (*) preparation of the reentry without return:
    #     delete all pre-condition fullfilled flags
    txt = ""
    for pre_context_sm_id in PreConditionIDList:
        txt += "    " + LanguageDB["$assignment"]("pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), 0)
    delete_pre_context_flags_str = txt

    #  -- execute 'on_failure' pattern action 
    #  -- goto initial state    
    end_of_stream_code_action_str, db = __adorn_action_code(EndOfStreamAction, SMD, SupportBeginOfLineF,
                                                            IndentationOffset=4)
    variable_db.update(db)

    # -- FAILURE ACTION: Under 'normal' circumstances the on_failure action is simply to be executed
    #                    since the 'get_forward()' incremented the 'current' pointer.
    #                    HOWEVER, when end of file has been reached the 'current' pointer has to
    #                    be reset so that the initial state can drop out on the buffer limit code
    #                    and then transit to the end of file action.
    # NOTE: It is possible that 'miss' happens after a chain of characters appeared. In any case the input
    #       pointer must be setup right after the lexeme start. This way, the lexer becomes a new chance as
    #       soon as possible.
    on_failure_str  = "me->buffer._input_p = me->buffer._lexeme_start_p;\n"
    on_failure_str += LanguageDB["$if"] + LanguageDB["$EOF"] + LanguageDB["$then"] + "\n"
    on_failure_str += "    " + LanguageDB["$comment"]("Next increment will stop on EOF character.") + "\n"
    on_failure_str += LanguageDB["$endif"] + "\n"
    on_failure_str += LanguageDB["$else"] + "\n"
    on_failure_str += "    " + LanguageDB["$comment"]("Step over nomatching character") + "\n"
    on_failure_str += "    " + LanguageDB["$input/increment"] + "\n"
    on_failure_str += LanguageDB["$endif"] + "\n"


    msg, db = __adorn_action_code(OnFailureAction, SMD, SupportBeginOfLineF,
                                  IndentationOffset=4)
    on_failure_str += msg
    variable_db.update(db)

    if False:
        # TO BE DELETED ____________________________________________________________________________________
        # -- routing to states via switch statement
        #    (note, the gcc computed goto is implement, too)
        txt = ""
        for state_index, state in sm.states.items():
            if state.transitions().is_empty(): continue
            txt += "            "
            txt += "case %i: " % int(state_index) + LanguageDB["$goto"]("$input", state_index) + "\n"

        if sm.core().pre_context_sm() != None:
            for state_index, state in sm.core().pre_context_sm().states.items():
                if state.transitions().is_empty(): continue
                txt += "            "
                txt += "case %i: " % int(state_index) + LanguageDB["$goto"]("$input", state_index) + "\n"

        switch_cases_drop_out_back_router_str = txt
        # TO BE DELETED ____________________________________________________________________________________

    if PreConditionIDList == []: precondition_involved_f = "0"
    else:                        precondition_involved_f = "1"

    txt = blue_print(__terminal_router_str,
            [["$$JUMPS_TO_ACCEPTANCE_STATE$$",    jumps_to_acceptance_states_str],   
             ["$$RESTORE_LAST_ACCEPTANCE_POS$$",  LanguageDB["$input/seek_position"]("last_acceptance_input_position")],
             ["$$TERMINAL_FAILURE-REF$$",         "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")],
             ["$$TERMINAL_FAILURE$$",             LanguageDB["$label"]("$terminal-FAILURE")],
            ])
                     
    txt += blue_print(__terminal_state_str, 
            [["$$SPECIFIC_TERMINAL_STATES$$",        specific_terminal_states_str],
                ["$$FAILURE_ACTION$$",               on_failure_str],
                ["$$END_OF_STREAM_ACTION$$",         end_of_stream_code_action_str],
                ["$$TERMINAL_END_OF_STREAM-DEF$$",   LanguageDB["$label-def"]("$terminal-EOF")],
                ["$$TERMINAL_FAILURE-DEF$$",         LanguageDB["$label-def"]("$terminal-FAILURE")],
                ["$$STATE_MACHINE_NAME$$",           SMD.name()],
                ["$$GOTO_START_PREPARATION$$",       LanguageDB["$goto"]("$re-start")],
                ])

    txt += blue_print(__on_continue_reentry_preparation_str,
                      [["$$REENTRY_PREPARATION$$",                    LanguageDB["$label-def"]("$re-start")],
                       ["$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$",  delete_pre_context_flags_str],
                       ["$$GOTO_START$$",                             LanguageDB["$goto"]("$start")],
                       ["$$COMMENT_ON_POST_CONTEXT_INITIALIZATION$$", comment_on_post_context_position_init_str],
                       ["$$TERMINAL_FAILURE-REF$$",                   "QUEX_LABEL(%i)" % get_address("$terminal-FAILURE")],
                       ])

    return txt, variable_db
    
def __frame_of_all(Code, Setup):
    LanguageDB = Setup.language_db
    namespace_open  = LanguageDB["$namespace-open"](Setup.analyzer_name_space)
    namespace_close = LanguageDB["$namespace-close"](Setup.analyzer_name_space)
    # namespace_ref   = LanguageDB["$namespace-ref"](Setup.analyzer_name_space)
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

    return "".join(["/* #include \"%s\"*/\n" % Setup.get_file_reference(Setup.output_header_file),
                    implementation_header_str,
                    "QUEX_NAMESPACE_MAIN_OPEN\n",
                    "QUEX_TYPE_CHARACTER  QUEX_NAME(LexemeNullObject) = (QUEX_TYPE_CHARACTER)0;\n",
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

def __require_terminating_zero_preparation(LanguageDB, CodeStr):
    CommentDelimiterList = LanguageDB["$comment-delimiters"]
    assert type(CommentDelimiterList) == list
    ObjectName = "Lexeme"

    for delimiter_info in CommentDelimiterList:
        assert type(delimiter_info) == list, "Argument 'CommentDelimiters' must be of type [[]]"
        assert len(delimiter_info) == 3, \
               "Elements of argument CommentDelimiters must be arrays with three elements:\n" + \
               "start of comment, end of comment, replacement string for comment.\n" + \
               "received: " + repr(delimiter_info)

    txt = CodeStr
    L       = len(txt)
    LO      = len(ObjectName)
    found_i = -1
    while 1 + 1 == 2:
        # TODO: Implement the skip_whitespace() function for more general treatment of Comment
        #       delimiters. Quotes for strings '"" shall then also be treate like comments.
        found_i = txt.find(ObjectName, found_i + 1)

        if found_i == -1: return False

        # Note: The variable must be named 'exactly' like the given name. 'xLexeme' or 'Lexemey'
        #       shall not trigger a treatment of 'Lexeme'.
        if     (found_i == 0      or not is_identifier_start(txt[found_i - 1]))     \
           and (found_i == L - LO or not is_identifier_continue(txt[found_i + LO])): 
               return True

def __set_last_acceptance(PatternID, __label_used_in_computed_goto_list_unique):
    __label_used_in_computed_goto_list_unique.add(get_address("$terminal-direct", PatternID))
    return "last_acceptance                = QUEX_LABEL(%i); /* Terminal %s */\n" \
           % (get_address("$terminal-direct", PatternID), PatternID)

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
    if Info.has_only_single_spaces():
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
        txt.append("case %s: " % case_label)
        txt.append(" " * (7 - len(case_label)))
        if next_i != L and CaseCodePairList[next_i][1] == code:
            txt.append("\n")
        else:
            txt.append(code + "\n")
            
    txt.append(0)
    txt.append("}\n")
    return txt


