from copy import copy
from quex.frs_py.string_handling import blue_print

import quex.core_engine.state_machine.index       as index
import quex.core_engine.generator.languages.label as label
#
from quex.core_engine.generator.action_info import ActionInfo


#________________________________________________________________________________
# C++
#
def __transition(StateMachineName, CurrentStateIdx, CurrentStateIsAcceptanceF, TargetStateIdx, 
                 OriginList, BackwardLexingF, BufferReloadRequiredOnDropOutF=True):
    """
        StateMachineName: Name of the state machine.

        TargetStateIdx: != None: Index of the state to which 'goto' has to go.
                        == None: Drop Out. Goto a terminal state.

        OriginList: List of origins. In case that a transition to a terminal state
                    is requested (TargetStateIdx==None), it may depend on
                    pre-conditions what terminal state is targeted. 

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
        return __transition_forward_lexing(StateMachineName, CurrentStateIdx, CurrentStateIsAcceptanceF, 
                                           TargetStateIdx, OriginList, BufferReloadRequiredOnDropOutF)
    
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

def __state_drop_out_code(StateMachineName, CurrentStateIdx, BackwardLexingF,
                          BufferReloadRequiredOnDropOutF,
                          CurrentStateIsAcceptanceF = None,
                          OriginList                = None):

    if BackwardLexingF: 
        return __state_drop_out_code_backward_lexing(StateMachineName, CurrentStateIdx,
                                                     BufferReloadRequiredOnDropOutF)
    else:
        return __state_drop_out_code_forward_lexing(StateMachineName, CurrentStateIdx,
                                                    BufferReloadRequiredOnDropOutF,
                                                    CurrentStateIsAcceptanceF = CurrentStateIsAcceptanceF,
                                                    OriginList                = OriginList)     

def __state_drop_out_code_backward_lexing(StateMachineName, CurrentStateIdx, 
                                          BufferReloadRequiredOnDropOutF):      
    txt = ""
    if BufferReloadRequiredOnDropOutF:
        txt += "#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING\n"
        txt += "if( backward_lexing_drop_out(me, input) ) " 
        txt += "goto %s; /* no adr. adaptions necessary */\n" % label.get_input(StateMachineName, CurrentStateIdx)
        txt += "#endif\n"

    #  -- general drop out: goto general terminal state
    txt += "goto %s;" % label.get_terminal(StateMachineName) 

    return txt

def __state_drop_out_code_forward_lexing(StateMachineName, CurrentStateIdx, 
                                         BufferReloadRequiredOnDropOutF,
                                         CurrentStateIsAcceptanceF, OriginList):        
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
    
    #     -- 'drop out' in non-acceptance --> goto general terminal
    if CurrentStateIsAcceptanceF == False:  
        txt += "goto %s;" % label.get_terminal(StateMachineName)
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
    t_txt = ""
    for origin in OriginList:   
        # -- pre-conditioned acceptance: check for correspondent flag which is supposed to be
        #    raised during the pre-condition check, some intelligent algo (see begin of line).
        terminal_label = label.get_terminal(StateMachineName, origin.state_machine_id)
        #
        if origin.pre_condition_id() != -1L:
            t_txt += "if( pre_condition_%s_fulfilled_f ) goto %s;\n" % (origin.state_machine_id, terminal_label)
            continue        
        
        elif origin.pre_condition_begin_of_line_f():
            t_txt += "if( me->begin_of_line_f ) goto %s;\n" % terminal_label
            continue
        
        elif origin.is_acceptance():    
            t_txt += "goto %s;\n" % terminal_label   # triggers conditionless
            break                                  # no need for further pre-condition consideration
            
    # -- double check for consistency
    if t_txt == "": raise "Acceptance state without acceptance origins!"        

    return txt + t_txt

def __transition_forward_lexing(StateMachineName, CurrentStateIdx, CurrentStateIsAcceptanceF, TargetStateIdx, OriginList,
                                BufferReloadRequiredOnDropOutF):
    """
       (1) If event triggers to subsequent state, one has to go there independent wether 
           the current state is an acceptance state or not.

       (2) If a 'drop out' occured in a non-acceptance state, then:
       
            -- TargetStateIdx == None (Normal Drop Out) 
               Goto the general terminal.
               There one determines the last pattern that won (if there is one).

       (3) If a 'drop out' in an acceptance state occured, the pre-conditions (if there are some
           determine which pattern has won, i.e. to what specific terminal state is to be gone.
           
    """
    
    # (*) Target State Defined (not a 'drop out') --> go there
    if TargetStateIdx != None:   
        return "goto %s;" % label.get(StateMachineName, TargetStateIdx)
    else:
        return "goto %s;" % label.get_drop_out(StateMachineName, CurrentStateIdx)

def __acceptance_info(OriginList, LanguageDB, BackwardLexingF):
    """Two cases:
       -- an origin marks an acceptance state without any post-condition:
          store input position and mark last acceptance state as the state machine of 
          the origin (note: this origin may result through a priorization)
       -- an origin marks an acceptance of an expression that has a post-condition.
          store the input position in a dedicated input position holder for the 
          origins state machine.
    """

    if BackwardLexingF:
        # (*) Backward Lexing 
        return __acceptance_info_backward_lexing(OriginList, LanguageDB)
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
                                      origin.pre_condition_begin_of_line_f() or
                                      origin.pre_condition_id() != -1L or
                                      origin.post_conditioned_acceptance_f(),
                                      OriginList)
    if inadmissible_origin_list != []:
        raise "Inadmissible origins for inverse state machine."
    #___________________________________________________________________________________________

    txt = "$/* origins = %s$*/" % repr(OriginList)
    #
    for origin in OriginList:
        if origin.store_input_position_f():
            txt += "pre_condition_%s_fulfilled_f = 1;\n" % repr(origin.state_machine_id).replace("L", "")           
    txt += "\n"    

    return txt

def __acceptance_info_forward_lexing(OriginList, LanguageDB):
    # check wether there is an non-acceptance state in the list, that
    # is neither a post nor a pre-condition
    important_origin_list = filter(lambda origin: 
                                   origin.is_acceptance() or
                                   origin.store_input_position_f(),
                                   OriginList)

    if important_origin_list == []:
        return ""

    txt = "$/* origins = %s$*/" % repr(OriginList)

    # -- get the pattern ids that indicate the start of a post-condition
    # -- get the pattern ids that indicate a pre-conditioned pattern 
    # -- get the first non-preconditioned, non-post-conditioned pattern 
    post_conditioned_pattern_id_list         = [] 
    pre_conditioned_pattern_id_list          = []
    unconditional_acceptance_pattern_id_list = []
    for origin in important_origin_list: 
        #   post condition flag 
        # + store input position flag 
        # => end of core pattern, now starts the post condition
        # (only post condition means: final end of pattern)
        if origin.post_conditioned_acceptance_f() and origin.store_input_position_f():
            post_conditioned_pattern_id_list.append(origin)
        elif origin.pre_condition_id() != -1L or origin.pre_condition_begin_of_line_f():
            pre_conditioned_pattern_id_list.append(origin)
        else:
            unconditional_acceptance_pattern_id_list.append(origin)
   
    # (*) write code to store input positions for post-conditions               
    for origin in post_conditioned_pattern_id_list:
        txt += LanguageDB["$input/tell_position"](origin.state_machine_id) + "\n"
    txt += "\n"     
        
    # (*) write code to handle pre-conditioned acceptance 
    #     Only those patterns are consider which have a higher priviledge 
    #     then any non-conditional pattern. Such a pattern wins unconditionally
    #     and further checks for other patterns are redundant.
    first_condition_f = True
    for origin in pre_conditioned_pattern_id_list:
        if first_condition_f: test_str = "$if CONDITION $then\nACTION $end\n"; first_condition_f = False    
        else:                 test_str = "$elseif CONDITION $then\nACTION $end\n"

        if origin.pre_condition_begin_of_line_f(): condition_str = " me->begin_of_line_f "
        else: condition_str = " pre_condition_%s_fulfilled_f " % origin.state_machine_id

        action_str = "    last_acceptance = %s;\n" % origin.state_machine_id
        # patterns that win on pre-conditions are absolute winners, not like 
        # post-conditioned patterns. there is no need for dedicated acceptance
        # positions for each pre-condition isolatedly.
        action_str += "    " + LanguageDB["$input/tell_position"]() + "\n"

        txt += blue_print(test_str, [["CONDITION", condition_str],
                                     ["ACTION",    action_str]])
        
    # (*) write code for the unconditional acceptance states
    indent_str = ""
    if unconditional_acceptance_pattern_id_list != []:
        if not first_condition_f: txt += "$else\n"; indent_str = "    "
        origin = unconditional_acceptance_pattern_id_list[0]
        txt +=  indent_str + "last_acceptance = %s;\n" % origin.state_machine_id
        # -- patterns where the post-condition succeeds do not have to store the 
        #    input position again. they take it from the time where the core pattern
        #    succeeded.
        if origin.store_input_position_f():
            txt += indent_str + LanguageDB["$input/tell_position"]() + "\n"
        if not first_condition_f: txt += "$end\n"

    txt += "\n"    
    return txt

def __tell_position(StateMachineID=None):
    if StateMachineID == None: msg = ""   
    else:                      msg = repr(StateMachineID).replace("L", "") + "_"
    
    return "QUEX_STREAM_TELL(last_acceptance_%sinput_position);" % msg 

def __label_definition(LabelName):
    return "  " + LabelName + ":"

__function_header_common = """
#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING
#    define $$QUEX_ANALYZER_STRUCT_NAME$$_on_buffer_reload(LoadedByteN)   \\
        /* Is this condition really necessary? <fschaef 07y7m26d> */      \\
        if( (QUEX_CHARACTER_TYPE*)last_acceptance_input_position != 0x0 ) \\
            last_acceptance_input_position -= LoadedByteN;                \\
                                                                          \\
$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$                

#endif  

#ifdef CONTINUE
#   undef CONTINUE
#endif
#define CONTINUE  goto QUEX_ANALYSER__$$STATE_MACHINE_NAME$$__REENTRY_PREPARATION
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
quex::$$QUEX_ANALYZER_STRUCT_NAME$$__$$STATE_MACHINE_NAME$$_analyser_function(QUEX_LEXER_CLASS* me) {
    // NOTE: Different modes correspond to different analyser functions. The analyser
    //       functions are all located inside the main class as static functions. That
    //       means, they are something like 'globals'. They receive a pointer to the 
    //       lexical analyser, since static member do not have access to the 'this' pointer.
    QUEX_LEXER_CLASS& self = *me;
    // static functions cannot access members, thus: create shortcuts
"""

__function_local_variable_definitions = """
    /*  me = pointer to state of the lexical analyser 
    */
    int                      last_acceptance = -1;
    QUEX_CHARACTER_POSITION  last_acceptance_input_position = (QUEX_CHARACTER_TYPE*)(0x00);
    /**/
    QUEX_CHARACTER_TYPE      input = (QUEX_CHARACTER_TYPE)(0x00);\n
    /**/
    QUEX_LEXEME_CHARACTER_TYPE*  Lexeme  = 0x0;
    size_t                       LexemeL = -1;
    /**/
#ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING
    int loaded_byte_n = 0; /* At transition Drop-Out: 
                           **    > 0  number of loaded bytes. 
                           **   == 0  'input' was not 'buffer limit code', no buffer reload happened.
                           */
#endif
   QUEX_ANALYSER__$$STATE_MACHINE_NAME$$__REENTRY_POINT:
"""

def __analyser_function(StateMachineName, EngineClassName, StandAloneEngineF,
                        function_body, PostConditionedStateMachineID_List, PreConditionIDList,
                        SupportBeginOfLineF, 
                        QuexEngineHeaderDefinitionFile, ModeNameList=[], InitialStateIndex=-1):   
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
    if SupportBeginOfLineF: 
        txt += "#define __QUEX_CORE_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION\n"

    txt += "#include<%s>\n" % QuexEngineHeaderDefinitionFile
    if StandAloneEngineF: 
        txt += __function_header_stand_alone
    else:                 
        txt += __function_header_quex_mode_based
        L = max(map(lambda name: len(name), ModeNameList))
        for name in ModeNameList:
            txt += "    quex::quex_mode&  %s%s = self.%s;\n" % \
                   (name, " " * (L- len(name)), name)


    txt += __function_local_variable_definitions
    txt = txt.replace("$$STATE_MACHINE_NAME$$", StateMachineName) 

    # -- post-condition position: store position of original pattern
    for state_machine_id in PostConditionedStateMachineID_List:
        txt += "    QUEX_CHARACTER_POSITION  last_acceptance_%s_input_position = (QUEX_CHARACTER_POSITION)(0x00);\n" % \
                repr(state_machine_id).replace("L", "")

    # -- smart buffers require a reload procedure to adapt the positions of pointers.
    #    recall, that the pointer point to memory and do not refer to stream positions.
    #    thus, they need to be adapted according to the loaded number of bytes
    load_procedure_txt = ""
    for state_machine_id in PostConditionedStateMachineID_List:
        load_procedure_txt += "        last_acceptance_%s_input_position -= (LoadedByteN); \\\n" % \
                              state_machine_id
    txt = txt.replace("$$QUEX_SUBTRACT_OFFSET_TO_LAST_ACCEPTANCE_??_POSITIONS$$", load_procedure_txt)                   

    # -- pre-condition fulfillment flags                
    for state_machine_id in PreConditionIDList:
        # get the state machine that the pre-condition serves:
        # -- get the state machine that represents the pre-condition
        pre_sm = index.get_state_machine_by_id(state_machine_id)
        # -- extract the original state machine that the pre-condition referes to.    
        pre_sm_origin_id = pre_sm.get_the_unique_original_state_machine_id()
        txt += "    int                        pre_condition_%s_fulfilled_f = 0;\n" \
               % repr(pre_sm_origin_id).replace("L", "")

    # -- entry to the actual function body
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
    txt += "        goto %s;\n" % label.get(StateMachineName, InitialStateIndex)

    txt += "    }\n"

    txt += "}\n"

    # -- the name of the game
    txt = txt.replace("$$QUEX_ANALYZER_STRUCT_NAME$$", EngineClassName)

    return txt

__terminal_state_str  = """
    // (*) terminal states
    //
    // Acceptance terminal states, i.e. the 'winner patterns'. This means
    // that the last input dropped out of a state where the longest matching
    // pattern was according to the terminal state. The terminal states are 
    // numbered after the pattern id.
    //
%%SPECIFIC_TERMINAL_STATES%%

  %%GENERAL_TERMINAL_STATE_LABEL%%: {
        int tmp = last_acceptance;
        //
        //  if last_acceptance => goto correspondent acceptance terminal state
        //  else               => execute defaul action
        //
        switch( tmp ) {
%%JUMPS_TO_ACCEPTANCE_STATE%%
            default:
               // no acceptance state    
               %%DEFAULT_ACTION%%
               goto QUEX_ANALYSER__%%STATE_MACHINE_NAME%%__REENTRY_PREPARATION;
        }
    }
QUEX_ANALYSER__%%STATE_MACHINE_NAME%%__REENTRY_PREPARATION:
    // (*) Common point for **restarting** lexical analysis.
    //     at each time when CONTINUE or YY_BREAK is called at the end of a pattern.
    //
    last_acceptance = -1;
%%DELETE_PRE_CONDITION_FULLFILLED_FLAGS%%
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
    goto QUEX_ANALYSER__%%STATE_MACHINE_NAME%%__REENTRY_POINT;
"""

def __terminal_states(StateMachineName, sm, action_db, DefaultAction, SupportBeginOfLineF, PreConditionIDList):
    """NOTE: During backward-lexing, for a pre-condition, there is not need for terminal
             states, since only the flag 'pre-condition fulfilled is raised.
    """      
    def __adorn_action_code(action_info, SupportBeginOfLineF): 
        ignored_code_regions = [["//", "\n", "\n"],   # c++ comments
                                ["/*", "*/", ""],     # c comments
                                ["\"", "\"", ""]]     # strings in quotes
        txt = ""
        # TODO: There could be a differenciation between a pattern that contains
        #       newline at the end, and those that do not. Then, there need not
        #       be a conditional question.
        if SupportBeginOfLineF:
            txt += "    QUEX_PREPARE_BEGIN_OF_LINE_CONDITION_FOR_NEXT_RUN\n"

        if action_info.contains_Lexeme_object(ignored_code_regions):
            txt += "    QUEX_PREPARE_LEXEME_OBJECT\n"
        else:
            txt += "    QUEX_DO_NOT_PREPARE_LEXEME_OBJECT\n"

        if action_info.contains_LexemeLength_object(ignored_code_regions):      
            txt += "    QUEX_PREPARE_LEXEME_LENGTH\n"

        txt += "    " + action_info.action_code().replace("\n", "\n    ") + "\n"  


        return txt

    # (*) specific terminal states of patterns (entered from acceptance states)
    txt = ""
    for state_machine_id, pattern_action_info in action_db.items():
        state_machine_id_str = repr(state_machine_id).replace("L", "")
        state_machine        = pattern_action_info.pattern_state_machine()
        action_code_orig     = pattern_action_info.action_code()
        #
        action_code = __adorn_action_code(pattern_action_info, SupportBeginOfLineF)
            
        # -- if the pattern is terminated after the post-condition, then the input
        #    has to be put back to the end of the 'core expression'.    
        post_condition_number_str = ""  
        if state_machine.is_post_conditioned(): post_condition_number_str =  state_machine_id_str + "_"
        #
        txt += "  %s:\n" % label.get_terminal(StateMachineName, state_machine_id)
        #
        txt += "    QUEX_STREAM_SEEK(last_acceptance_%sinput_position);\n" % post_condition_number_str
        # -- paste the action code that correponds to the pattern   
        txt += action_code + "\n"    
        txt += "    CONTINUE;  // == goto QUEX_ANALYZER__%s__REENTRY_PREPARATION\n" % StateMachineName
        
    specific_terminal_states_str = txt

    # (*) general terminal state (entered from non-acceptance state)    
    txt = ""    
    for state_machine_id in action_db.keys():
        txt += "     case %s: goto %s;\n" % (repr(state_machine_id), 
                                             label.get_terminal(StateMachineName, state_machine_id))
    jumps_to_acceptance_states_str = txt

    # (*) preparation of the reentry without return:
    #     delete all pre-condition fullfilled flags
    delete_pre_condition_flags_str = ""
    for state_machine_id in PreConditionIDList:
        # get the state machine that the pre-condition serves:
        # -- get the state machine that represents the pre-condition
        pre_sm = index.get_state_machine_by_id(state_machine_id)
        # -- extract the original state machine that the pre-condition referes to.    
        pre_sm_origin_id = pre_sm.get_the_unique_original_state_machine_id()
        delete_pre_condition_flags_str += "    pre_condition_%s_fulfilled_f = 0;\n" \
                                          % repr(pre_sm_origin_id).replace("L", "")

    #  -- execute default pattern action 
    #  -- reset character stream to last success                
    #  -- goto initial state    
    default_action_str = __adorn_action_code(ActionInfo(-1, DefaultAction), SupportBeginOfLineF)
    txt = blue_print(__terminal_state_str, 
                     [["%%JUMPS_TO_ACCEPTANCE_STATE%%",    jumps_to_acceptance_states_str],   
                      ["%%SPECIFIC_TERMINAL_STATES%%",     specific_terminal_states_str],
                      ["%%DEFAULT_ACTION%%",               default_action_str],
                      ["%%GENERAL_TERMINAL_STATE_LABEL%%", label.get_terminal(StateMachineName, None)],
                      ["%%STATE_MACHINE_NAME%%",           StateMachineName],
                      ["%%INITIAL_STATE_INDEX_LABEL%%",    label.get(StateMachineName, sm.init_state_index)],
                      ["%%DELETE_PRE_CONDITION_FULLFILLED_FLAGS%%", delete_pre_condition_flags_str]])

    return txt
    
def __pre_condition_ok(PreConditionStateMachineID):
    return "pre_condition_%s_fulfilled_f = 1;" % repr(PreConditionStateMachineID).replace("L", "")   
