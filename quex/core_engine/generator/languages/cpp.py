from copy import copy
from quex.frs_py.string_handling import blue_print

import quex.core_engine.state_machine.index as index
#
from quex.core_engine.generator.action_info import ActionInfo

def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")

#________________________________________________________________________________
# C++
#

__header_definitions_txt = """
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/template/Analyser>

#ifdef CONTINUE
#   undef CONTINUE
#endif
#define CONTINUE  $$GOTO_START_PREPARATION$$
"""

def __header_definitions(LanguageDB):

    txt = __header_definitions_txt
    txt = txt.replace("$$GOTO_START_PREPARATION$$", LanguageDB["$goto"]("$re-start"))
    return txt

def __local_variable_definitions(VariableInfoList):
    txt = ""
    L = max(map(lambda info: len(info[0]), VariableInfoList))
    for info in VariableInfoList:
        type  = info[0]
        name  = info[1]
        value = info[2]
        txt += "    %s%s %s = %s;\n" % (type, " " * (L-len(type)), name, value)
    return txt
         

__function_signature = """
TEMPLATE_IN __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE  
$$QUEX_ANALYZER_STRUCT_NAME$$_$$STATE_MACHINE_NAME$$_analyser_function(MINIMAL_ANALYZER_TYPE* me) 
{
    // NOTE: Different modes correspond to different analyser functions. The analyser
    //       functions are all located inside the main class as static functions. That
    //       means, they are something like 'globals'. They receive a pointer to the 
    //       lexical analyser, since static member do not have access to the 'this' pointer.
#   if defined (__QUEX_SETTING_PLAIN_C)
#      define self (*me)
#   else
       MINIMAL_ANALYZER_TYPE& self = *me;
#   endif
"""


def __analyser_function(StateMachineName, EngineClassName, StandAloneEngineF,
                        function_body, PostConditionedStateMachineID_List, PreConditionIDList,
                        ModeNameList=[], InitialStateIndex=-1, LanguageDB=None):   
    """EngineClassName = name of the structure that contains the engine state.
                         if a mode of a complete quex environment is created, this
                         is the mode name. otherwise, any name can be chosen. 
       StandAloneEngineF = False if a mode for a quex engine is to be created. True
                           if a stand-alone lexical engine is required (without the
                           complete mode-handling framework of quex).
        
       NOTE: If a stand-alone lexer is requested, then there are two functions that are
             created additionally: 

               'EngineClassName'_init(EngineClassName* me,
                                      CharacterCarrierType StartInputPosition);

                     This function has to be called before starting the lexing process.
                     See the unit tests for examples.
               
               'EngineClassName'_do(EngineClassName* me);
                     
                     This function does a lexical analysis from the current position as
                     it is stored in 'me'.
    """              
    txt = ""

    local_variable_list = []
    signature = __function_signature

    if not StandAloneEngineF: 
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            local_variable_list.append(["quex::quex_mode&", name + " " * (L- len(name)), 
                                        "QUEX_LEXER_CLASS::" + name]) 

    txt  = "#include <quex/code_base/temporary_macros_on>\n"
    txt += __load_procedure(PostConditionedStateMachineID_List)
    txt += signature
    txt  = txt.replace("$$STATE_MACHINE_NAME$$", StateMachineName) 

    txt += "    " + LanguageDB["$comment"]("me = pointer to state of the lexical analyser") + "\n"

    local_variable_list.extend(
            [ ["QUEX_GOTO_LABEL_TYPE",         "last_acceptance",                "QUEX_GOTO_TERMINAL_LABEL_INIT_VALUE"],
              ["QUEX_CHARACTER_POSITION_TYPE", "last_acceptance_input_position", "(CharacterCarrierType*)(0x00)"],
              ["CharacterCarrierType",         "input",                          "(CharacterCarrierType)(0x00)"]
            ])
              
    # -- post-condition position: store position of original pattern
    for state_machine_id in PostConditionedStateMachineID_List:
         local_variable_list.append(["QUEX_CHARACTER_POSITION_TYPE",
                                     "last_acceptance_%s_input_position" % __nice(state_machine_id),
                                     "(QUEX_CHARACTER_POSITION_TYPE)(0x00)"])

    # -- pre-condition fulfillment flags                
    for pre_context_sm_id in PreConditionIDList:
        local_variable_list.append(["int", "pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), "0"])

    txt += __local_variable_definitions(local_variable_list)
    txt += "#   ifdef QUEX_OPTION_ACTIVATE_ASSERTS\n"
    txt += "    me->DEBUG_analyser_function_at_entry = me->current_analyser_function;\n"
    txt += "#   endif\n"

    txt += LanguageDB["$label-def"]("$start")

    # -- entry to the actual function body
    txt += "    QuexBuffer_mark_lexeme_start(&me->buffer);\n"
    txt += "    QuexBuffer_undo_terminating_zero_for_lexeme(&me->buffer);\n";
    
    txt += function_body

    # -- prevent the warning 'unused variable'
    txt += "\n"
    txt += "    // prevent compiler warning 'unused variable': use variables once in a part of the code\n"
    txt += "    // that is never reached (and deleted by the compiler anyway).\n"
    txt += "    if( 0 == 1 ) {\n"
    txt += "        int unused = 0;\n"
    for mode_name in ModeNameList:
        txt += "        unused = unused + %s.id;\n" % mode_name
    ## This was once we did not know ... if there was a goto to the initial state or not.
    ## txt += "        goto %s;\n" % label.get(StateMachineName, InitialStateIndex)

    txt += "    }\n"

    txt += "}\n"

    # -- the name of the game
    txt = txt.replace("$$QUEX_ANALYZER_STRUCT_NAME$$", EngineClassName)

    txt += "#include <quex/code_base/temporary_macros_off>\n"
    return txt


__buffer_reload_str = """
TEMPLATE_IN bool 
$$QUEX_ANALYZER_STRUCT_NAME$$_$$STATE_MACHINE_NAME$$_buffer_reload_forward(BUFFER_FILLER_TYPE* filler, 
                                             QUEX_CHARACTER_POSITION_TYPE* last_acceptance_input_position
                                             $$LAST_ACCEPTANCE_POSITIONS$$)
{
    if( filler == 0x0 ) return false;
    const size_t LoadedByteN = QuexBufferFiller_load_forward(filler);
    if( LoadedByteN == 0 ) return false;

    if( *last_acceptance_input_position != 0x0 ) { 
        *last_acceptance_input_position -= LoadedByteN;
        // QUEX_DEBUG_ADR_ASSIGNMENT("last_acceptance_input_position", *last_acceptance_input_position); 
    }                                                                  
                                                                          
$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$                
    return true;
}
"""

def __load_procedure(PostConditionedStateMachineID_List):
    # Reload requires to adapt the positions of pointers.
    # Pointers point to memory and do not refer to stream positions.
    # thus, they need to be adapted according to the loaded number of bytes
    adapt_txt = ""
    argument_list = ""
    for state_machine_id in PostConditionedStateMachineID_List:
        variable_name  = "last_acceptance_%s_input_position" % state_machine_id 
        adapt_txt     += "       *%s -= (LoadedByteN); \\\n"  % variable_name
        argument_list += ", QUEX_CHARACTER_POSITION_TYPE* %s"         % variable_name

    return blue_print(__buffer_reload_str,
                  [["$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$", adapt_txt],
                   ["$$LAST_ACCEPTANCE_POSITIONS$$", argument_list]])

__terminal_state_str  = """
  // (*) Terminal states _______________________________________________________
  //
  // Acceptance terminal states, i.e. the 'winner patterns'. This means
  // that the last input dropped out of a state where the longest matching
  // pattern was according to the terminal state. The terminal states are 
  // numbered after the pattern id.
  //
#define Lexeme       (me->buffer._lexeme_start_p)
#define LexemeBegin  (me->buffer._lexeme_start_p)
#define LexemeEnd    (me->buffer._input_p)
#define LexemeL      (size_t)(me->buffer._input_p - me->buffer._lexeme_start_p)
$$SPECIFIC_TERMINAL_STATES$$

$$TERMINAL_END_OF_STREAM-DEF$$
$$END_OF_STREAM_ACTION$$
#ifdef __QUEX_OPTION_ANALYSER_RETURN_TYPE_IS_VOID
        return /*TKN_TERMINATION*/;
#else
        return TKN_TERMINATION;
#endif

$$TERMINAL_DEFAULT-DEF$$
$$DEFAULT_ACTION$$
        $$GOTO_START_PREPARATION$$

#undef Lexeme
#undef LexemeBegin
#undef LexemeEnd
#undef LexemeL
#ifndef __QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED
__TERMINAL_ROUTER: {
        //  if last_acceptance => goto correspondent acceptance terminal state
        //  else               => execute defaul action
        switch( last_acceptance ) {
$$JUMPS_TO_ACCEPTANCE_STATE$$
            default: $$TERMINAL_DEFAULT-GOTO$$; /* nothing matched */
        }
    }
#endif // __QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED
"""

__on_continue_reentry_preparation_str = """
  
$$REENTRY_PREPARATION$$
    // (*) Common point for **restarting** lexical analysis.
    //     at each time when CONTINUE is called at the end of a pattern.
    //
    last_acceptance = QUEX_GOTO_TERMINAL_LABEL_INIT_VALUE;
$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$
    //
    //  If a mode change happened, then the function must first return and
    //  indicate that another mode function is to be called. At this point, 
    //  we to force a 'return' on a mode change. 
    //
    //  Pseudo Code: if( previous_mode != current_mode ) {
    //                   return 0;
    //               }
    // 
    //  When the analyzer returns, the caller function has to watch if a mode change
    //  occured. If not it can call this function again.
    //
#   ifdef QUEX_OPTION_ACTIVATE_ASSERTS
    if( me->DEBUG_analyser_function_at_entry != me->current_analyser_function ) {
        fprintf(stderr, "Mode change without immediate return from the lexical analyser.");
        exit(-1);
    }
#   endif
    $$GOTO_START$$
"""

def __adorn_action_code(action_info, SupportBeginOfLineF, IndentationOffset=4): 
    indentation = " " * IndentationOffset 
    ignored_code_regions = [["//", "\n", "\n"],   # c++ comments
                            ["/*", "*/", ""],     # c comments
                            ["\"", "\"", ""]]     # strings in quotes
    txt = ""
    # TODO: There could be a differenciation between a pattern that contains
    #       newline at the end, and those that do not. Then, there need not
    #       be a conditional question.
    if SupportBeginOfLineF:
        txt += indentation + "QuexBuffer_store_last_character_of_lexeme_for_next_run(&me->buffer);\n"

    if action_info.contains_variable("Lexeme", ignored_code_regions):
        txt += indentation + "QuexBuffer_set_terminating_zero_for_lexeme(&me->buffer);\n"

    txt += indentation + "{\n"
    txt += indentation + "    " + action_info.action_code().replace("\n", "\n        ") + "\n"  
    txt += indentation + "}\n"

    return txt

def get_terminal_code(state_machine_id, pattern_action_info, SupportBeginOfLineF, 
                      LanguageDB, DirectlyReachedTerminalID_List):
    txt = ""
    state_machine_id_str = __nice(state_machine_id)
    state_machine        = pattern_action_info.pattern_state_machine()
    action_code_orig     = pattern_action_info.action_code()
    #
    action_code = __adorn_action_code(pattern_action_info, SupportBeginOfLineF)
        
    # (*) The 'normal' terminal state can also be reached by the terminal
    #     router and, thus, **must** restore the acceptance input position. This is so, 
    #     because when the 'goto last_acceptance' is triggered the 'last_acceptance'
    #     may lay backwards and needs to be restored.
    txt += LanguageDB["$label-def"]("$terminal", state_machine_id) + "\n"

    # (1) Retrieving the input position for the next run
    #     NOTE: The different scenarios differ in the way they can 'offer' an entry
    #           to the terminal without restoring the input position. This 'direct'
    #           entry is useful for direct transitions to a terminal where there
    #           acceptance position is clear.
    if state_machine.core().post_context_backward_input_position_detector_sm() != None:
        # Pseudo Ambiguous Post Contexts:
        # -- require that the end of the core pattern is to be searched! One 
        #    cannot simply restore some stored input position.
        # -- The pseudo-ambiguous post condition is translated into a 'normal'
        #    pattern. However, after a match a backward detection of the end
        #    of the core pattern is done. Here, we first need to go to the point
        #    where the 'normal' pattern ended, then we can do a backward detection.
        txt += "    " + LanguageDB["$input/seek_position"]("last_acceptance_input_position") + "\n"
        txt += LanguageDB["$label-def"]("$terminal-direct", state_machine_id) + "\n"
        txt += "    PAPC_input_postion_backward_detector_%s(me);\n" % \
               __nice(state_machine.core().post_context_backward_input_position_detector_sm_id())

    elif state_machine.core().post_context_id() != -1L: 
        # Post Contexted Patterns:
        txt += LanguageDB["$label-def"]("$terminal-direct", state_machine_id) + "\n"
        # -- have a dedicated register from where they store the end of the core pattern.
        variable = "last_acceptance_%s_input_position" % __nice(state_machine_id)
        txt += "    " + LanguageDB["$input/seek_position"](variable) + "\n"

    else:
        # Normal Acceptance:
        # -- only restore the input position
        txt += "    " + LanguageDB["$input/seek_position"]("last_acceptance_input_position") + "\n"
        txt += LanguageDB["$label-def"]("$terminal-direct", state_machine_id) + "\n"



    # -- paste the action code that correponds to the pattern   
    txt += action_code + "\n"    
    txt += "    " + LanguageDB["$goto"]("$re-start") + "\n" 
    txt += "\n"

    return txt

def __terminal_states(StateMachineName, sm, action_db, DefaultAction, EndOfStreamAction, 
                      SupportBeginOfLineF, PreConditionIDList, LanguageDB, 
                      DirectlyReachedTerminalID_List):
    """NOTE: During backward-lexing, for a pre-condition, there is not need for terminal
             states, since only the flag 'pre-condition fulfilled is raised.
    """      

    # (*) specific terminal states of patterns (entered from acceptance states)
    txt = ""
    for state_machine_id, pattern_action_info in action_db.items():
        txt += get_terminal_code(state_machine_id, pattern_action_info, SupportBeginOfLineF, 
                                 LanguageDB, DirectlyReachedTerminalID_List)
    specific_terminal_states_str = txt

    # (*) general terminal state (entered from non-acceptance state)    
    txt = ""    
    for state_machine_id in action_db.keys():
        txt += "            case %s: " % repr(state_machine_id).replace("L", "")
        txt += LanguageDB["$goto"]("$terminal", state_machine_id) + "\n"
    jumps_to_acceptance_states_str = txt

    # (*) preparation of the reentry without return:
    #     delete all pre-condition fullfilled flags
    txt = ""
    for pre_context_sm_id in PreConditionIDList:
        txt += "    " + LanguageDB["$assignment"]("pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), 0)
    delete_pre_context_flags_str = txt

    #  -- execute default pattern action 
    #  -- goto initial state    
    end_of_stream_code_action_str = __adorn_action_code(ActionInfo(-1, EndOfStreamAction), SupportBeginOfLineF,
                                                        IndentationOffset=16)
    # -- DEFAULT ACTION: Under 'normal' circumstances the default action is simply to be executed
    #                    since the 'get_forward()' incremented the 'current' pointer.
    #                    HOWEVER, when end of file has been reached the 'current' pointer has to
    #                    be reset so that the initial state can drop out on the buffer limit code
    #                    and then transit to the end of file action.
    default_action_str  = LanguageDB["$if EOF"] + "\n"
    default_action_str += "    " + LanguageDB["$input/decrement"] + "\n"
    default_action_str += LanguageDB["$endif"] + "\n"
    default_action_str += LanguageDB["$else"] + "\n"
    default_action_str += "    " + LanguageDB["$comment"]("Step over nomatching character")
    default_action_str += "    " + LanguageDB["$input/increment"] + "\n"
    default_action_str += LanguageDB["$endif"] + "\n"
    default_action_str += __adorn_action_code(ActionInfo(-1, DefaultAction), SupportBeginOfLineF,
                                              IndentationOffset=16)

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

    if PreConditionIDList == []: precondition_involved_f = "0"
    else:                        precondition_involved_f = "1"

    txt = blue_print(__terminal_state_str, 
                     [["$$JUMPS_TO_ACCEPTANCE_STATE$$",    jumps_to_acceptance_states_str],   
                      ["$$SPECIFIC_TERMINAL_STATES$$",     specific_terminal_states_str],
                      ["$$DEFAULT_ACTION$$",               default_action_str],
                      ["$$END_OF_STREAM_ACTION$$",         end_of_stream_code_action_str],
                      ["$$TERMINAL_END_OF_STREAM-DEF$$",   LanguageDB["$label-def"]("$terminal-EOF")],
                      ["$$TERMINAL_DEFAULT-DEF$$",         LanguageDB["$label-def"]("$terminal-DEFAULT")],
                      ["$$TERMINAL_GENERAL-DEF$$",         LanguageDB["$label-def"]("$terminal-general", False)],
                      ["$$TERMINAL_DEFAULT-GOTO$$",        LanguageDB["$goto"]("$terminal-DEFAULT")],
                      ["$$STATE_MACHINE_NAME$$",           StateMachineName],
                      ["$$GOTO_START_PREPARATION$$",       LanguageDB["$goto"]("$re-start")],
                      ])

    txt += blue_print(__on_continue_reentry_preparation_str,
                      [["$$REENTRY_PREPARATION$$",                   LanguageDB["$label-def"]("$re-start")],
                       ["$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$", delete_pre_context_flags_str],
                       ["$$GOTO_START$$",                            LanguageDB["$goto"]("$start")],
                       ])

    return txt
    
