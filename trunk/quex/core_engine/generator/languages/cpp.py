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
#ifndef __QUEX_ENGINE_HEADER_DEFINITIONS
#   if    defined(__GNUC__) \
       && ((__GNUC__ > 2) || (__GNUC__ == 2 && __GNUC_MINOR__ >= 3))
#       if ! defined(__QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED)
#           define __QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED
#       endif
#   endif
#   ifdef __QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED

        typedef  void*    QUEX_GOTO_LABEL_TYPE;
#       define QUEX_GOTO_TERMINAL_LABEL_INIT_VALUE       &&TERMINAL_DEFAULT
#       define QUEX_GOTO_STATE_LABEL_INIT_VALUE          (0x0)
#       define QUEX_SET_drop_out_state_index(StateIndex) drop_out_state_index = &&STATE_ ##StateIndex ##_INPUT; 
#       define QUEX_SET_last_acceptance(TerminalIndex)   last_acceptance      = &&TERMINAL_ ##TerminalIndex; 
#       define QUEX_GOTO_drop_out_state_index()          goto *drop_out_state_index;
#       define QUEX_GOTO_last_acceptance()               goto *last_acceptance;

#   else
        typedef  uint32_t QUEX_GOTO_LABEL_TYPE;
#       define QUEX_GOTO_TERMINAL_LABEL_INIT_VALUE       (-1)
#       define QUEX_GOTO_STATE_LABEL_INIT_VALUE          (-1)
#       define QUEX_SET_drop_out_state_index(StateIndex) do drop_out_state_index = StateIndex; 
#       define QUEX_SET_last_acceptance(TerminalIndex)   last_acceptance         = TerminalIndex; 
#       define QUEX_GOTO_drop_out_state_index()          goto __DROP_OUT_STATE_ROUTER;
#       define QUEX_GOTO_last_acceptance()               goto __TERMINAL_ROUTER;
#   endif

#   include "$$INCLUDE$$"
#   define __QUEX_ENGINE_HEADER_DEFINITIONS

#   ifdef CONTINUE
#      undef CONTINUE
#   endif
#   define CONTINUE  $$GOTO_START_PREPARATION$$

#endif
"""
def __header_definitions(IncludeFile, LanguageDB):
    txt = __header_definitions_txt.replace("$$INCLUDE$$", IncludeFile)
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
         
__function_header_common = """
#define $$QUEX_ANALYZER_STRUCT_NAME$$_on_buffer_reload(LoadedByteN)         \\
        /* Is this condition really necessary? <fschaef 07y7m26d> */        \\
        if( (QUEX_CHARACTER_TYPE*)last_acceptance_input_position != 0x0 ) { \\
            last_acceptance_input_position -= LoadedByteN;                  \\
            QUEX_DEBUG_ADR_ASSIGNMENT("last_acceptance_input_position", last_acceptance_input_position); \\
        }                                                                   \\
                                                                            \\
$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$                

"""

__function_header_stand_alone = __function_header_common + """
typedef QUEX_CORE_ANALYSER_STRUCT  $$QUEX_ANALYZER_STRUCT_NAME$$;

/* Protect against redefinition if more than one analyser function is defined 
** inside the same source code file.
*/
#ifndef __DEFINITION_GUARD__QUEX_CORE_ENGINE_INITIALIZATION_FUNCTION_DEFINED__
#define __DEFINITION_GUARD__QUEX_CORE_ENGINE_INITIALIZATION_FUNCTION_DEFINED__
void (*$$QUEX_ANALYZER_STRUCT_NAME$$_init)(QUEX_CORE_ANALYSER_STRUCT_init_ARGUMENT_LIST)
     = QUEX_CORE_ANALYSER_STRUCT_init;
#endif     

QUEX_INLINE_KEYWORD
QUEX_ANALYSER_RETURN_TYPE
$$QUEX_ANALYZER_STRUCT_NAME$$_do(QUEX_CORE_ANALYSER_STRUCT* me) 
{
"""

__function_header_quex_mode_based = __function_header_common + """
QUEX_ANALYSER_RETURN_TYPE
quex::$$QUEX_ANALYZER_STRUCT_NAME$$_$$STATE_MACHINE_NAME$$_analyser_function(QUEX_LEXER_CLASS* me) 
{
    // NOTE: Different modes correspond to different analyser functions. The analyser
    //       functions are all located inside the main class as static functions. That
    //       means, they are something like 'globals'. They receive a pointer to the 
    //       lexical analyser, since static member do not have access to the 'this' pointer.
    QUEX_LEXER_CLASS& self = *me;
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
                                      QUEX_CHARACTER_TYPE StartInputPosition);

                     This function has to be called before starting the lexing process.
                     See the unit tests for examples.
               
               'EngineClassName'_do(EngineClassName* me);
                     
                     This function does a lexical analysis from the current position as
                     it is stored in 'me'.
    """              
    txt = ""
    local_variable_list = []
    if StandAloneEngineF: 
        txt += __function_header_stand_alone
    else:                 
        txt += __function_header_quex_mode_based
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            local_variable_list.append(["quex::quex_mode&", name + " " * (L- len(name)), "QUEX_LEXER_CLASS::" + name]) 

    txt = txt.replace("$$STATE_MACHINE_NAME$$", StateMachineName) 
    txt += "    " + LanguageDB["$comment"]("me = pointer to state of the lexical analyser") + "\n"

    local_variable_list.extend(
            [ ["QUEX_GOTO_LABEL_TYPE",        "last_acceptance",                "QUEX_GOTO_TERMINAL_LABEL_INIT_VALUE"],
              ["QUEX_GOTO_LABEL_TYPE",        "drop_out_state_index",           "QUEX_GOTO_STATE_LABEL_INIT_VALUE"],
              ["QUEX_CHARACTER_POSITION",     "last_acceptance_input_position", "(QUEX_CHARACTER_TYPE*)(0x00)"],
              ["QUEX_CHARACTER_TYPE",         "input",                          "(QUEX_CHARACTER_TYPE)(0x00)"], 
              ["QUEX_LEXEME_CHARACTER_TYPE*", "Lexeme",                         "0x0"],
              ["size_t",                      "LexemeL",                        "-1"],
              ["int",                         "loaded_byte_n",                  "-1"]])
              
    # -- post-condition position: store position of original pattern
    for state_machine_id in PostConditionedStateMachineID_List:
         local_variable_list.append(["QUEX_CHARACTER_POSITION",
                                     "last_acceptance_%s_input_position" % __nice(state_machine_id),
                                     "(QUEX_CHARACTER_POSITION)(0x00)"])

    # -- pre-condition fulfillment flags                
    for pre_context_sm_id in PreConditionIDList:
        local_variable_list.append(["int", "pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), "0"])

    txt += __local_variable_definitions(local_variable_list)

    txt += LanguageDB["$label-def"]("$start")

    # -- smart buffers require a reload procedure to adapt the positions of pointers.
    #    recall, that the pointer point to memory and do not refer to stream positions.
    #    thus, they need to be adapted according to the loaded number of bytes
    load_procedure_txt = ""
    for state_machine_id in PostConditionedStateMachineID_List:
        load_procedure_txt += "        last_acceptance_%s_input_position -= (LoadedByteN); \\\n" % \
                              state_machine_id
    txt = txt.replace("$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$", load_procedure_txt)                   

    # -- entry to the actual function body
    txt += "    QUEX_CORE_MARK_LEXEME_START();\n"
    txt += "    QUEX_UNDO_PREPARE_LEXEME_OBJECT();\n";
    
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

    return txt

__terminal_state_str  = """
  // (*) Terminal states _______________________________________________________
  //
  // Acceptance terminal states, i.e. the 'winner patterns'. This means
  // that the last input dropped out of a state where the longest matching
  // pattern was according to the terminal state. The terminal states are 
  // numbered after the pattern id.
  //
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

#ifndef __QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED
__TERMINAL_ROUTER:
$$TERMINAL_GENERAL-DEF$$ {
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
    __QUEX_CORE_OPTION_RETURN_ON_DETECTED_MODE_CHANGE
    $$GOTO_START$$
"""

__drop_out_buffer_reload_handler = """
__FORWARD_DROP_OUT_HANDLING:
    // Since all drop out states work the same, we introduce here a 'router' that
    // jumps to a particular state based on the setting of a variable: drop_out_state_index.
    loaded_byte_n = QUEX_BUFFER_LOAD_FORWARD();
    if( loaded_byte_n != -1 ) {
        $$QUEX_ANALYZER_STRUCT_NAME$$_on_buffer_reload(loaded_byte_n);
        QUEX_GOTO_drop_out_state_index();
    }
    // no load possible (EOF) => (i)  goto general terminal
    //                           (ii) init state triggers EOF action
    QUEX_GOTO_last_acceptance();

#if $$SWITCH_BACKWARD_LEXING_INVOLVED$$
__BACKWARD_DROP_OUT_HANDLING:
    QUEX_BUFFER_LOAD_BACKWARD();
    if( ! QUEX_BEGIN_OF_FILE() ) { 
        // no re-computation required, since we're not in 'normal lexing mode'
        QUEX_GOTO_drop_out_state_index();
    }
    $$GOTO-TERMINAL_GENERAL_BACKWARD$$
#endif

#if ! defined(__QUEX_OPTION_GNU_C_GREATER_2_3_DETECTED)
__DROP_OUT_ROUTING:
    switch( drop_out_state_index ) {
$$SWITCH_CASES_DROP_OUT_ROUTE_BACK_TO_STATE$$
    }
#endif
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
        txt += indentation + "QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN();\n"

    if action_info.contains_Lexeme_object(ignored_code_regions):
        txt += indentation + "QUEX_PREPARE_LEXEME_OBJECT();\n"

    if action_info.contains_LexemeLength_object(ignored_code_regions):      
        txt += indentation + "QUEX_PREPARE_LEXEME_LENGTH();\n"

    txt += indentation + "{\n"
    txt += indentation + "    " + action_info.action_code().replace("\n", "\n        ") + "\n"  
    txt += indentation + "}\n"

    return txt

def get_terminal_code(state_machine_id, pattern_action_info, SupportBeginOfLineF, 
                      LanguageDB, 
                      DirectlyReachedTerminalID_List):
    txt = ""
    state_machine_id_str = __nice(state_machine_id)
    state_machine        = pattern_action_info.pattern_state_machine()
    action_code_orig     = pattern_action_info.action_code()
    #
    action_code = __adorn_action_code(pattern_action_info, SupportBeginOfLineF)
        
    #
    if state_machine_id in DirectlyReachedTerminalID_List:
        txt += LanguageDB["$label-def"]("$terminal-with-preparation", state_machine_id) + "\n"
        #
        if state_machine.core().post_context_backward_input_position_detector_sm() == None:
            # we need to position the current_p to the next character to be read
            # (NOTE: dedicated terminals only exist for forward lexical analysis)
            txt += LanguageDB["$input/increment"] + "\n"

    txt += LanguageDB["$label-def"]("$terminal", state_machine_id) + "\n"

    # -- if the pattern is terminated after the post-condition, then the input
    #    has to be put back to the end of the 'core expression' **in any case**    
    if state_machine.core().post_context_id() != -1L: 
        post_context_number_str = state_machine_id_str + "_"
        txt += "    " + LanguageDB["$input/seek_position"](
                "last_acceptance_%sinput_position" % post_context_number_str) + "\n"

    else:
        # NOTE: The pseudo-ambiguous post condition is translated into a 'normal'
        #       pattern. However, after a match a backward detection of the end
        #       of the core pattern is done. Here, we first need to go to the point
        #       where the 'normal' pattern ended, then we can do a backward detection.
        txt += "    " + LanguageDB["$input/seek_position"]("last_acceptance_input_position") + "\n"

    if state_machine.core().post_context_backward_input_position_detector_sm() != None:
        txt += "    PAPC_input_postion_backward_detector_%s(me);\n" % \
               __nice(state_machine.core().post_context_backward_input_position_detector_sm_id())

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

    txt += blue_print(__drop_out_buffer_reload_handler, 
                      [["$$SWITCH_CASES_DROP_OUT_ROUTE_BACK_TO_STATE$$", switch_cases_drop_out_back_router_str],
                       ["$$SWITCH_BACKWARD_LEXING_INVOLVED$$",           precondition_involved_f],
                       ["$$GOTO-TERMINAL_GENERAL_FORWARD$$",   LanguageDB["$goto"]("$terminal-general", False)],
                       ["$$GOTO-TERMINAL_GENERAL_BACKWARD$$",  LanguageDB["$goto"]("$terminal-general", True)]
                       ])
    return txt
    
