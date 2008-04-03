from copy import copy
from quex.frs_py.string_handling import blue_print

import quex.core_engine.state_machine.index       as index
import quex.core_engine.generator.languages.label as label
from   quex.core_engine.generator.languages.label import __nice
#
from quex.core_engine.generator.action_info import ActionInfo


#________________________________________________________________________________
# C++
#
def __transition(StateMachineName, CurrentStateIdx, TargetStateIdx, 
                 BackwardLexingF, BufferReloadRequiredOnDropOutF=True):
    """
        StateMachineName: Name of the state machine.

        TargetStateIdx: != None: Index of the state to which 'goto' has to go.
                        == None: Drop Out. Goto a terminal state.

        BackwardLexingF: Flag indicating wether this function is called during 
                         normal forward lexing, or for the implementation of a 
                         backwards state machine (complex pre-conditions).

        BufferReloadRequiredOnDropOutF: If a state has no transitions, no input is taken 
                         from the input stream. Therefore, at this point, the buffer reload
                         is also nonsense. This flag tells, if code for buffer reload is required
                         or not in the case of a drop out.
    """
    if BackwardLexingF: 
        return __transition_backward_lexing(StateMachineName, CurrentStateIdx, TargetStateIdx, 
                                            BufferReloadRequiredOnDropOutF)
    else:
        return __transition_forward_lexing(StateMachineName, CurrentStateIdx, TargetStateIdx)
    
def __transition_backward_lexing(StateMachineName, CurrentStateIdx, TargetStateIdx, BufferReloadRequiredOnDropOutF):
    """Backward lexiging state transitions are simple, there are only two cases:

       (1) A particular subsequent state is specified for the trigger. 
           In this case, goto this particular state (which is not a terminal state).
       (2) No particular subsequent state is specified. This signals a 'drop out'
           situation. 

       Normally, on 'drop out' one either:

           -- goes to a specific terminal state of the winning pattern, or
           -- goes to the general terminal state that determines the last pattern that won.

       During backward lexing, though, there are **no winning patterns**. All patterns that ever
       matched are indicated through there 'pre-condition-fulfilled flag'. This flag is set at 
       the entry of an acceptance state. Further, no pattern actions are performed on when pre-
       conditions are determined. So, no specific terminal states are necessary, all transitions
       can directly enter the general terminal state. Absolutely nothing is left to be done at the
       general terminal state. Thus, the last two cases are combined into one, see above.
    """
    
    # (*) Target State Defined: go there
    if TargetStateIdx >= 0:
        return "goto %s;" % label.get(StateMachineName, TargetStateIdx)
    else:
        return "goto %s;" % label.get_drop_out(StateMachineName, CurrentStateIdx)

def __transition_forward_lexing(StateMachineName, CurrentStateIdx, TargetStateIdx):
    """
       (1) If event triggers to subsequent state, one has to go there independent wether 
           the current state is an acceptance state or not.

       (2) If a 'drop out' occured in a non-acceptance state, then:
       
            -- TargetStateIdx == None (Normal Drop Out) 
               Goto the general terminal.
               There one determines the last pattern that won (if there is one).

       (3) If a 'drop out' in an acceptance state occured, the pre-conditions (if there are some
           determine which pattern has won, i.e. to what specific terminal state is to be gone.
           This will happen inside the drop out region.
           
    """
    
    # (*) Target State Defined (not a 'drop out') --> go there
    if TargetStateIdx == None:   
        return "goto %s;" % label.get_drop_out(StateMachineName, CurrentStateIdx)
    elif TargetStateIdx == "END_OF_FILE":
        return "goto TERMINAL_END_OF_STREAM;" 
    else:
        return "goto %s;" % label.get(StateMachineName, TargetStateIdx)

def __acceptance_info(OriginList, LanguageDB, BackwardLexingF, 
                      BackwardInputPositionDetectionF=False):
    """Two cases:
       -- an origin marks an acceptance state without any post-condition:
          store input position and mark last acceptance state as the state machine of 
          the origin (note: this origin may result through a priorization)
       -- an origin marks an acceptance of an expression that has a post-condition.
          store the input position in a dedicated input position holder for the 
          origins state machine.
    """
    if BackwardInputPositionDetectionF: assert BackwardLexingF

    if BackwardLexingF:
        # (*) Backward Lexing 
        if not BackwardInputPositionDetectionF:
            return __acceptance_info_backward_lexing(OriginList, LanguageDB)
        else:
            return __acceptance_info_backward_lexing_find_core_pattern(OriginList, LanguageDB)

    else:
        # (*) Forward Lexing 
        return __acceptance_info_forward_lexing(OriginList, LanguageDB)

def __acceptance_info_backward_lexing(OriginList, LanguageDB):
    """Backward Lexing:
       -- Using an inverse state machine from 'real' current start position backwards
          until a drop out occurs.
       -- During backward lexing, there is no 'winner' so all origins that indicate
          acceptance need to be considered. They raise there flag 'pre-condition fulfilled'.
    """
    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert inadmissible_origin_list == [], \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    txt = LanguageDB["$comment"](" origins = %s" % repr(OriginList)) + "\n"
    #
    for origin in OriginList:
        if origin.store_input_position_f():
            txt += "pre_context_%s_fulfilled_f = 1;\n" % __nice(origin.state_machine_id)
    txt += "\n"    

    return txt

def __acceptance_info_backward_lexing_find_core_pattern(OriginList, LanguageDB):
    """Backward Lexing:
       -- (see above)
       -- for the search of the end of the core pattern, the acceptance position
          backwards must be stored. 
       -- There is only one pattern involved, so no determination of 'who won'
          is important.
    """
    # There should be nothing, but unconditional acceptances or no-acceptance 
    # origins in the list of origins.
    inadmissible_origin_list = filter(lambda origin:
                                      origin.pre_context_begin_of_line_f() or
                                      origin.pre_context_id() != -1L or
                                      origin.post_context_id() != -1L,
                                      OriginList)
    assert inadmissible_origin_list == [], \
           "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    txt = LanguageDB["$comment"](" origins = %s" % repr(OriginList)) + "\n"
    #
    for origin in OriginList:
        if origin.store_input_position_f():
            txt += "QUEX_STREAM_TELL(end_of_core_pattern_position);\n"

    return txt

def __state_drop_out_code(StateMachineName, CurrentStateIdx, BackwardLexingF,
                          BufferReloadRequiredOnDropOutF,
                          CurrentStateIsAcceptanceF = None,
                          OriginList                = None,
                          LanguageDB                = None,
                          DropOutTargetStateID      = -1L):

    txt = "__QUEX_DEBUG_INFO_DROP_OUT(%i);\n" % CurrentStateIdx
    if BackwardLexingF: 
        txt += __state_drop_out_code_backward_lexing(StateMachineName, CurrentStateIdx,
                                                     BufferReloadRequiredOnDropOutF,
                                                     DropOutTargetStateID)
    else:
        txt += __state_drop_out_code_forward_lexing(StateMachineName, CurrentStateIdx,
                                                    BufferReloadRequiredOnDropOutF,
                                                    CurrentStateIsAcceptanceF = CurrentStateIsAcceptanceF,
                                                    OriginList           = OriginList,
                                                    LanguageDB           = LanguageDB,
                                                    DropOutTargetStateID = DropOutTargetStateID)     

    return txt

def __state_drop_out_code_backward_lexing(StateMachineName, CurrentStateIdx, 
                                          BufferReloadRequiredOnDropOutF, 
                                          DropOutTargetStateID):      
    txt = ""
    if BufferReloadRequiredOnDropOutF:
        txt += "#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING\n"
        txt += "if( backward_lexing_drop_out(me, input) ) " 
        txt += "goto %s; /* no adr. adaptions necessary */\n" % label.get_input(StateMachineName, CurrentStateIdx)
        txt += "#endif\n"

    if DropOutTargetStateID != -1L:
        # -- A 'match all' is implemented as 'drop out to target'. This happens
        #    in order to ensure that the buffer limits are checked.
        txt += "goto %s;" % label.get(StateMachineName, DropOutTargetStateID)
        return txt
    
    #  -- general drop out: goto general terminal state
    txt += "goto %s;\n" % label.get_terminal(StateMachineName) 

    return txt

def __state_drop_out_code_forward_lexing(StateMachineName, CurrentStateIdx, 
                                         BufferReloadRequiredOnDropOutF,
                                         CurrentStateIsAcceptanceF, OriginList, LanguageDB,
                                         DropOutTargetStateID):      
    txt = ""
    if BufferReloadRequiredOnDropOutF:
        txt += "#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING\n"
        txt += "loaded_byte_n = forward_lexing_drop_out(me, input);\n"
        txt += "if( loaded_byte_n ) {\n" 
        txt += "    $$QUEX_ANALYZER_STRUCT_NAME$$_on_buffer_reload(loaded_byte_n);\n"
        txt += "    goto %s;\n" % label.get_input(StateMachineName, CurrentStateIdx)
        txt += "}\n"
        txt += "#endif\n"

    # From here on: input is not a 'buffer limit code' 
    #               (i.e. input does **not** mean: 'load buffer')
    if DropOutTargetStateID != -1L:
        # -- A 'match all' is implemented as 'drop out to target'. This happens
        #    in order to ensure that the buffer limits are checked.
        txt += "goto %s;" % label.get(StateMachineName, DropOutTargetStateID)
        return txt
    
    #     -- 'drop out' in non-acceptance --> goto general terminal
    if CurrentStateIsAcceptanceF == False:  
        txt += "goto %s;\n" % label.get_terminal(StateMachineName)
        return txt
     
    #    -- 'drop out' in acceptance state --> check pre-conditions (if there are some)
    #                                      --> goto first specific terminal that either
    #                                          fulfills pre-condition or is unconditional
    #  NOTE: As soon as an unconditional acceptance occures there is no need
    #        for checking further pre-conditions, since they are outruled.
    #  NOTE: Maybe, there is a potential of reducing the code size a little, if 
    #        only those acceptance positions are adapted that are possibly reached
    #        at this point. This, though, would require some analysis of the state machine.
    #        The effect is probably minimal and only makes sense if there are many, many
    #        post conditions.
    #
    def __on_detection_code(StateMachineName, Origin):
        txt = "__QUEX_DEBUG_INFO_ACCEPTANCE(%i);\n" % Origin.state_machine_id
        terminal_label = label.get_terminal(StateMachineName, Origin.state_machine_id)
        return txt + "goto %s;\n" % terminal_label

    t_txt = get_acceptance_detector(OriginList, __on_detection_code,
                                    LanguageDB, StateMachineName)
            
    # -- double check for consistency
    assert t_txt != "", "Acceptance state without acceptance origins!"        

    return txt + t_txt

def __acceptance_info_forward_lexing(OriginList, LanguageDB):

    txt = LanguageDB["$comment"](" origins = %s" % repr(OriginList)) + "\n"
    # -- get the pattern ids that indicate the start of a post-condition
    #    (i.e. the end of a core pattern where a post condition is to follow).
    # -- collect patterns that reach acceptance at this state.
    final_acceptance_origin_list     = []
    for origin in OriginList: 
        if origin.is_end_of_post_contexted_core_pattern():
            # store current input position, to be restored when post condition really matches
            txt += LanguageDB["$input/tell_position"](origin.state_machine_id) + "\n"
        elif origin.is_acceptance():
            final_acceptance_origin_list.append(origin)
   
    def __on_detection_code(StateMachineName, Origin):
        info  = "__QUEX_DEBUG_INFO_ACCEPTANCE(%i);\n" % Origin.state_machine_id
        info += LanguageDB["$assignment"]("last_acceptance", __nice(Origin.state_machine_id))
        # NOTE: When post conditioned patterns end they do not store the input position.
        #       Rather, the acceptance position of the core pattern is considered.
        if Origin.store_input_position_f():
            info += LanguageDB["$input/tell_position"]() + "\n"
        return info

    txt += get_acceptance_detector(final_acceptance_origin_list, __on_detection_code,
                                   LanguageDB)

    return txt

def get_acceptance_detector(OriginList, get_on_detection_code_fragment, 
                            LanguageDB, StateMachineName=""):
        
    def indent_this(Fragment):
        # do not replace the last '\n' with '\n    '
        return "    " + Fragment[:-1].replace("\n", "\n    ") + Fragment[-1]

    txt = ""
    if_statement = LanguageDB["$if"]
    OriginList.sort()
    for origin in OriginList:
        if not origin.is_acceptance(): continue

        info = get_on_detection_code_fragment(StateMachineName, origin)

        if origin.pre_context_id() != -1L:
            txt += if_statement + " pre_context_%s_fulfilled_f " % origin.pre_context_id() + LanguageDB["$then"] + "\n" 
            txt += indent_this(info)
            txt += LanguageDB["$end"] + "\n"
        
        elif origin.pre_context_begin_of_line_f():
            txt += if_statement + " $begin-of-line-flag-true " + LanguageDB["$then"] + "\n"  
            txt += indent_this(info)
            txt += LanguageDB["$end"] + "\n"
        
        else:
            if if_statement == LanguageDB["$if"]: 
                txt += info
            else:
                # if an 'if' statements preceeded, the acceptance needs to appear in an else block
                txt += LanguageDB["$else"] + "\n"; 
                txt += indent_this(info)
                txt += LanguageDB["$end"] + "\n"

            break  # no need for further pre-condition consideration

        if_statement = LanguageDB["$elseif"]

    # (*) write code for the unconditional acceptance states
    return txt

def __tell_position(StateMachineID=None):
    if StateMachineID == None: msg = ""   
    else:                      msg = __nice(StateMachineID) + "_"
    
    return "QUEX_STREAM_TELL(last_acceptance_%sinput_position);" % msg 

def __label_definition(LabelName):
    return "  " + LabelName + ":"

__header_definitions_txt = """
#ifndef __QUEX_ENGINE_HEADER_DEFINITIONS
#   include "$$INCLUDE$$"
#   define __QUEX_ENGINE_HEADER_DEFINITIONS

#   ifdef __QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS

#      define __QUEX_PRINT_SOURCE_POSITION()                 \\
        std::fprintf(stderr, "%s:%i: \\t", __FILE__, __LINE__);            

#      define __QUEX_DEBUG_INFO_START_LEXING(Name)              \\
              __QUEX_PRINT_SOURCE_POSITION()                    \\
              std::fprintf(stderr, "START:    %s\\n", #Name)

#      define __QUEX_DEBUG_INFO_ENTER(StateIdx)                 \\
              __QUEX_PRINT_SOURCE_POSITION()                    \\
              std::fprintf(stderr, "enter:    %i\\n", (int)StateIdx)

#      define __QUEX_DEBUG_INFO_DROP_OUT(StateIdx)              \\
              __QUEX_PRINT_SOURCE_POSITION()                    \\
              std::fprintf(stderr, "drop:     %i\\n", (int)StateIdx)

#      define __QUEX_DEBUG_INFO_ACCEPTANCE(StateIdx)            \\
              __QUEX_PRINT_SOURCE_POSITION()                    \\
              std::fprintf(stderr, "accept:   %i\\n", (int)StateIdx)

#      define __QUEX_DEBUG_INFO_TERMINAL(Terminal)             \\
              __QUEX_PRINT_SOURCE_POSITION()                   \\
              std::fprintf(stderr, "terminal: %s\\n", #Terminal)

#      define __QUEX_DEBUG_INFO_INPUT(Character)                             \\
              __QUEX_PRINT_SOURCE_POSITION()                                 \\
                Character == '\\n' ? std::fprintf(stderr, "input:    '\\\\n'\\n") \\
              : Character == '\\t' ? std::fprintf(stderr, "input:    '\\\\t'\\n") \\
              :                      std::fprintf(stderr, "input:    '%c'\\n", (char)Character) 
#   else
#      define __QUEX_DEBUG_INFO_START_LEXING(Name)   /* empty */
#      define __QUEX_DEBUG_INFO_ENTER(StateIdx)      /* empty */
#      define __QUEX_DEBUG_INFO_DROP_OUT(StateIdx)   /* empty */
#      define __QUEX_DEBUG_INFO_ACCEPTANCE(StateIdx) /* empty */
#      define __QUEX_DEBUG_INFO_TERMINAL(Terminal)   /* empty */
#      define __QUEX_DEBUG_INFO_INPUT(Character)     /* empty */
#   endif

#   ifdef CONTINUE
#      undef CONTINUE
#   endif
#   define CONTINUE  goto __REENTRY_PREPARATION

#endif
"""
def __header_definitions(IncludeFile):
    return __header_definitions_txt.replace("$$INCLUDE$$", IncludeFile)

def __local_variable_definitions(VariableInfoList):
    txt = ""
    for info in VariableInfoList:
        type  = info[0]
        name  = info[1]
        value = info[2]
        txt += "    %s %s = %s;\n" % (type, name, value)
    return txt
         

__function_header_common = """
#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING
#    define $$QUEX_ANALYZER_STRUCT_NAME$$_on_buffer_reload(LoadedByteN)   \\
        /* Is this condition really necessary? <fschaef 07y7m26d> */      \\
        if( (QUEX_CHARACTER_TYPE*)last_acceptance_input_position != 0x0 ) \\
            last_acceptance_input_position -= LoadedByteN;                \\
                                                                          \\
$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$                

#endif  
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
$$QUEX_ANALYZER_STRUCT_NAME$$_do(QUEX_CORE_ANALYSER_STRUCT* me) {
"""

__function_header_quex_mode_based = __function_header_common + """
QUEX_ANALYSER_RETURN_TYPE
quex::$$QUEX_ANALYZER_STRUCT_NAME$$_$$STATE_MACHINE_NAME$$_analyser_function(QUEX_LEXER_CLASS* me) {
    // NOTE: Different modes correspond to different analyser functions. The analyser
    //       functions are all located inside the main class as static functions. That
    //       means, they are something like 'globals'. They receive a pointer to the 
    //       lexical analyser, since static member do not have access to the 'this' pointer.
    QUEX_LEXER_CLASS& self = *me;
    // static functions cannot access members, thus: create shortcuts
"""

__analyzer_function_start = """
#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING
    int loaded_byte_n = 0; /* At transition Drop-Out: 
                           **    > 0  number of loaded bytes. 
                           **   == 0  'input' was not 'buffer limit code', no buffer reload happened.
                           */
#endif
   __QUEX_DEBUG_INFO_START_LEXING($$QUEX_ANALYZER_STRUCT_NAME$$);
   __REENTRY_POINT:
"""

def __analyser_function(StateMachineName, EngineClassName, StandAloneEngineF,
                        function_body, PostConditionedStateMachineID_List, PreConditionIDList,
                        ModeNameList=[], InitialStateIndex=-1):   
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
            local_variable_list.append(["quex::quex_mode&", name + " " * (L- len(name)), "self." + name]) 

    txt = txt.replace("$$STATE_MACHINE_NAME$$", StateMachineName) 
    txt += "/*  me = pointer to state of the lexical analyser */"

    local_variable_list.extend(
            [ ["int",                         "last_acceptance",                "-1"],
              ["QUEX_CHARACTER_POSITION",     "last_acceptance_input_position", "(QUEX_CHARACTER_TYPE*)(0x00)"],
              ["QUEX_CHARACTER_TYPE",         "input",                          "(QUEX_CHARACTER_TYPE)(0x00)"], 
              ["QUEX_LEXEME_CHARACTER_TYPE*", "Lexeme",                         "0x0"],
              ["size_t",                      "LexemeL",                        "-1"] ])
              
    # -- post-condition position: store position of original pattern
    for state_machine_id in PostConditionedStateMachineID_List:
         local_variable_list.append(["QUEX_CHARACTER_POSITION",
                                     "last_acceptance_%s_input_position" % __nice(state_machine_id),
                                     "(QUEX_CHARACTER_POSITION)(0x00)"])

    # -- pre-condition fulfillment flags                
    for pre_context_sm_id in PreConditionIDList:
        local_variable_list.append(["int", "pre_context_%s_fulfilled_f" % __nice(pre_context_sm_id), "0"])

    txt += __local_variable_definitions(local_variable_list)

    txt += __analyzer_function_start

    # -- smart buffers require a reload procedure to adapt the positions of pointers.
    #    recall, that the pointer point to memory and do not refer to stream positions.
    #    thus, they need to be adapted according to the loaded number of bytes
    load_procedure_txt = ""
    for state_machine_id in PostConditionedStateMachineID_List:
        load_procedure_txt += "        last_acceptance_%s_input_position -= (LoadedByteN); \\\n" % \
                              state_machine_id
    txt = txt.replace("$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$", load_procedure_txt)                   

    # -- entry to the actual function body
    txt += "    QUEX_CORE_ANALYSER_STRUCT_mark_lexeme_start(me);\n"
    txt += "    QUEX_UNDO_PREPARE_LEXEME_OBJECT;\n";
    
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

    txt = "    " + txt.replace("\n", "\n    ")
    if txt[-4:] == "    ": txt = txt[:-4]

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

  TERMINAL_END_OF_STREAM:
$$END_OF_STREAM_ACTION$$

  TERMINAL_DEFAULT:
$$DEFAULT_ACTION$$
        goto __REENTRY_PREPARATION;

  $$GENERAL_TERMINAL_STATE_LABEL$$: {
        int tmp = last_acceptance;
        //
        //  if last_acceptance => goto correspondent acceptance terminal state
        //  else               => execute defaul action
        //
        __QUEX_DEBUG_INFO_TERMINAL(General);
        switch( tmp ) {
$$JUMPS_TO_ACCEPTANCE_STATE$$
            default: goto TERMINAL_DEFAULT; /* nothing matched */
        }
    }

  
  __REENTRY_PREPARATION:
    // (*) Common point for **restarting** lexical analysis.
    //     at each time when CONTINUE is called at the end of a pattern.
    //
    last_acceptance = -1;
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
    goto __REENTRY_POINT;
"""

def __terminal_states(StateMachineName, sm, action_db, DefaultAction, EndOfStreamAction, 
                      SupportBeginOfLineF, PreConditionIDList):
    """NOTE: During backward-lexing, for a pre-condition, there is not need for terminal
             states, since only the flag 'pre-condition fulfilled is raised.
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
            txt += indentation + "QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN\n"

        if action_info.contains_Lexeme_object(ignored_code_regions):
            txt += indentation + "QUEX_PREPARE_LEXEME_OBJECT\n"
        else:
            txt += indentation + "QUEX_DO_NOT_PREPARE_LEXEME_OBJECT\n"

        if action_info.contains_LexemeLength_object(ignored_code_regions):      
            txt += indentation + "QUEX_PREPARE_LEXEME_LENGTH\n"

        txt += indentation + "{\n"
        txt += indentation + "    " + action_info.action_code().replace("\n", "\n        ") + "\n"  
        txt += indentation + "}\n"

        return txt

    # (*) specific terminal states of patterns (entered from acceptance states)
    txt = ""
    for state_machine_id, pattern_action_info in action_db.items():
        state_machine_id_str = __nice(state_machine_id)
        state_machine        = pattern_action_info.pattern_state_machine()
        action_code_orig     = pattern_action_info.action_code()
        #
        action_code = __adorn_action_code(pattern_action_info, SupportBeginOfLineF)
            
        # -- if the pattern is terminated after the post-condition, then the input
        #    has to be put back to the end of the 'core expression'.    
        post_context_number_str = ""  
        if state_machine.core().post_context_id() != -1L: 
            post_context_number_str = state_machine_id_str + "_"
        #
        txt += "  %s:\n" % label.get_terminal(StateMachineName, state_machine_id)
        txt += "    __QUEX_DEBUG_INFO_TERMINAL(%s);\n" % __nice(state_machine_id)
        #
        if state_machine.core().post_context_backward_input_position_detector_sm() == None:
            txt += "    QUEX_STREAM_SEEK(last_acceptance_%sinput_position);\n" % \
                   post_context_number_str
        else:
            # NOTE: The pseudo-ambiguous post condition is translated into a 'normal'
            #       pattern. However, after a match a backward detection of the end
            #       of the core pattern is done. Here, we first need to go to the point
            #       where the 'normal' pattern ended, then we can do a backward detection.
            txt += "    QUEX_STREAM_SEEK(last_acceptance_input_position);\n"
            txt += "    PAPC_input_postion_backward_detector_%s(me);\n" % \
                   __nice(state_machine.core().post_context_backward_input_position_detector_sm_id())
        # -- paste the action code that correponds to the pattern   
        txt += action_code + "\n"    
        txt += "    goto __REENTRY_PREPARATION;\n" # % StateMachineName
        txt += "\n"
        
    specific_terminal_states_str = txt

    # (*) general terminal state (entered from non-acceptance state)    
    txt = ""    
    for state_machine_id in action_db.keys():
        txt += "            case %s: goto %s;\n" % \
                (repr(state_machine_id), 
                      label.get_terminal(StateMachineName, state_machine_id))

    jumps_to_acceptance_states_str = txt

    # (*) preparation of the reentry without return:
    #     delete all pre-condition fullfilled flags
    delete_pre_context_flags_str = ""
    for pre_context_sm_id in PreConditionIDList:
        delete_pre_context_flags_str += "    pre_context_%s_fulfilled_f = 0;\n" \
                                        % __nice(pre_context_sm_id)

    #  -- execute default pattern action 
    #  -- reset character stream to last success                
    #  -- goto initial state    
    default_action_str = __adorn_action_code(ActionInfo(-1, DefaultAction), SupportBeginOfLineF,
                                             IndentationOffset=16)
    end_of_stream_code_action_str = __adorn_action_code(ActionInfo(-1, EndOfStreamAction), SupportBeginOfLineF,
                                                        IndentationOffset=16)

    txt = blue_print(__terminal_state_str, 
                     [["$$JUMPS_TO_ACCEPTANCE_STATE$$",    jumps_to_acceptance_states_str],   
                      ["$$SPECIFIC_TERMINAL_STATES$$",     specific_terminal_states_str],
                      ["$$DEFAULT_ACTION$$",               default_action_str],
                      ["$$END_OF_STREAM_ACTION$$",         end_of_stream_code_action_str],
                      ["$$GENERAL_TERMINAL_STATE_LABEL$$", label.get_terminal(StateMachineName, None)],
                      ["$$STATE_MACHINE_NAME$$",           StateMachineName],
                      ["$$INITIAL_STATE_INDEX_LABEL$$",    label.get(StateMachineName, sm.init_state_index)],
                      ["$$DELETE_PRE_CONDITION_FULLFILLED_FLAGS$$", delete_pre_context_flags_str]])

    return txt
    
def __pre_context_ok(PreConditionStateMachineID):
    return "pre_context_%s_fulfilled_f = 1;" % __nice(PreConditionStateMachineID)
