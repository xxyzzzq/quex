from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator
import quex.core_engine.state_machine.core                as     state_machine 
#
from   quex.core_engine.generator.languages.core import __nice
from   quex.input.setup                          import setup as Setup

LanguageDB = None

def do(State, StateIdx, SMD, ForceSaveLastAcceptanceF=False):
    assert isinstance(State, state_machine.State)
    assert isinstance(SMD,   StateMachineDecorator)
    global LanguageDB

    LanguageDB = Setup.language_db
    
    mode = SMD.mode()
    if   mode == "ForwardLexing":                  return forward_lexing(State, StateIdx, SMD, ForceSaveLastAcceptanceF)
    elif mode == "BackwardLexing":                 return backward_lexing(State.origins().get_list())
    elif mode == "BackwardInputPositionDetection": return backward_lexing_find_core_pattern(State.origins().get_list())
    else:
        assert False, "This part of the code should never be reached"

def forward_lexing(State, StateIdx, SMD, ForceSaveLastAcceptanceF=False):
    """Forward Lexing:

       (1) Pure 'Store-Input-Position' States

           States that mark the end of a core pattern that is followed by a post
           condition. If such a state reached, then the current position needs 
           to be stored in a dedicated register---ultimatively.

       (2) 'Real'-Acceptance States

           States that terminate an analyzis step and declare the winning pattern.

           -- No pre-conditions, or all pre-conditions have lower priority than
              the highest priority non-pre-condition 
              
              => decision of who wins can be made at code-generation time.

           -- High-priority pre-conditions involved 

              => code must select from all pre-conditions that have higher
                 priority than the first non-pre-conditioned pattern.
           
           => use 'get_acceptance_detector()' in order to get a sequence of 'if-else'
              blocks that determine acceptance. 
    """
    assert SMD.__class__.__name__ == "StateMachineDecorator"
    LanguageDB = Setup.language_db

    OriginList = State.origins().get_list()

    # (1) Set the post context registers (if appropriate)
    txt = __handle_post_conditioned_core_patterns(OriginList, SMD)

    # -- If there is no 'real' acceptance, then we're done
    #    (Post conditioned core pattern end states are not in itself 
    #     cannot be acceptance states. If the state is an acceptance 
    #     state than there must be 'real' acceptance origins.)
    if not State.is_acceptance(): 
        return txt 

    # -- If the current acceptance does not need to be stored, then do not do it
    if     not ForceSaveLastAcceptanceF \
       and not subsequent_states_require_save_last_acceptance(StateIdx, State, SMD.sm()): 
        return txt
   
    # (2) Create detector for normal and pre-conditioned acceptances
    def __on_detection_code(Origin):
        """Store the name of the winner pattern (last_acceptance) and the position
           where it has matched (use of $input/tell_position).
        """
        if type(Origin) == type(None):
            # Case if no un-conditional acceptance occured, then register nothing
            return ""

        assert Origin.is_acceptance()

        info = LanguageDB["$set-last_acceptance"](__nice(Origin.state_machine_id))
        # NOTE: When a post conditioned pattern ends it does not need to store the input 
        #       position. Rather, the acceptance position of the core pattern is retrieved
        #       in the terminal state.
        if Origin.post_context_id() == -1:
             info += LanguageDB["$input/tell_position"]("last_acceptance_input_position") + "\n"

        return info

    txt.append(get_acceptance_detector(OriginList, __on_detection_code))

    return txt

def __handle_post_conditioned_core_patterns(OriginList, SMD):
    """Creates code to store the input position for post conditioned
       core patterns. That means, that the input pointer must return
       to this place in case that the post condition is fulfilled.
    """
    global LanguageDB

    # (1) Set the post context registers (if appropriate)
    #     (also determine the list of acceptance origins)
    txtl = []
    for origin in OriginList: 
        if origin.is_end_of_post_contexted_core_pattern():
            # Assumption about origin based on assumption about single pattern state machine:
            #
            #    According to 'setup_post_context.py' (currently line 121) no acceptance
            #    state of a post context can store the input position. This has been made 
            #    impossible! Otherwise, the post context would have zero length.
            #
            #    Post-conditions via backward search, i.e. pseudo ambigous post conditions,
            #    are a different ball-game.
            #
            assert origin.is_acceptance() == False

            # Store current input position, to be restored when post condition really matches
            post_context_index = SMD.get_post_context_index(origin.state_machine_id)
            txtl += [
                    "    ", 
                    LanguageDB["$comment"]("post context index '%s' == state machine '%s'" % \
                            (__nice(post_context_index), __nice(origin.state_machine_id))),
                    "    ", 
                    LanguageDB["$input/tell_position"]("post_context_start_position[%i]\n" % \
                            post_context_index)
                    ]

    return txtl

def backward_lexing(OriginList):
    """Backward Lexing:
       -- Using an inverse state machine from 'real' current start position backwards
          until a drop out occurs.
       -- During backward lexing, there is no 'winner' so all origins that indicate
          acceptance need to be considered. They raise there flag 'pre-condition fulfilled'.
    """
    LanguageDB = Setup.language_db

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

    txt = []
    for origin in OriginList:
        if not origin.store_input_position_f(): continue
        assert origin.is_acceptance()
        variable = "pre_context_%s_fulfilled_f" % __nice(origin.state_machine_id)
        txt.append("    " + LanguageDB["$assignment"](variable, 1))
    txt.append("\n")

    return txt

def backward_lexing_find_core_pattern(OriginList):
    """Backward Lexing:
       -- (see above)
       -- for the search of the end of the core pattern, the acceptance position
          backwards must be stored. 
       -- There is only one pattern involved, so no determination of 'who won'
          is important.
    """
    LanguageDB = Setup.language_db

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


    for origin in OriginList:
        if origin.store_input_position_f():
            assert origin.is_acceptance()
            return ["    ", LanguageDB["$input/tell_position"]("end_of_core_pattern_position"), "\n"]
    return ["\n"]

def get_acceptance_detector(OriginList, get_on_detection_code_fragment):
        
    # Just try, to make sure that the function has thought about the case 
    # 'no unconditional_case_treated_f' option.
    assert get_on_detection_code_fragment(None) != None

    LanguageDB = Setup.language_db

    def indent_this(Fragment):
        # do not replace the last '\n' with '\n    '
        return "    " + Fragment[:-1].replace("\n", "\n    ") + Fragment[-1]

    txt = []
    first_if_statement_f         = True
    unconditional_case_treated_f = False
    OriginList.sort()
    for origin in OriginList:
        if not origin.is_acceptance(): continue

        info = get_on_detection_code_fragment(origin)

        if origin.pre_context_id() != -1L:
            if first_if_statement_f: txt.append(LanguageDB["$if pre-context"](origin.pre_context_id()))
            else:                    txt.append(LanguageDB["$elseif pre-context"](origin.pre_context_id()))
            txt.append(indent_this(info))
            txt.append(LanguageDB["$endif"])
        
        elif origin.pre_context_begin_of_line_f():
            if first_if_statement_f: txt.append(LanguageDB["$if begin-of-line"])
            else:                    txt.append(LanguageDB["$elseif begin-of-line"])
            txt.append(indent_this(info))
            txt.append(LanguageDB["$endif"] )
        
        else:
            if first_if_statement_f: 
                txt.append(info)
            else:
                # if an 'if' statements preceeded, the acceptance needs to appear in an else block
                txt.append(LanguageDB["$else"])
                txt.append("\n")
                txt.append(indent_this(info))
                txt.append(LanguageDB["$endif"])
            unconditional_case_treated_f = True
            break  # no need for further pre-condition consideration

        first_if_statement_f = False

    if unconditional_case_treated_f == False:
        txt.append(get_on_detection_code_fragment(None))

    result = "".join(txt)
    if len(result) == 0: return ""
    else:                return "    " + result[:-1].replace("\n", "\n    ") + result[-1]

def subsequent_states_require_save_last_acceptance(StateIdx, State, SM):
    """For the 'longest match' approach it is generally necessary to store the last
       pattern that has matched the current input stream. This means, that the
       current pattern index **and** the current input position need to be stored.
       Nothing of that is necessary, if one knows that a state does not have any
       'critical' follow-up states where the position is to be restored. For example,

                 (0)--- 'a' --->(( 1 ['a'] ))---- 'b' --->(( 2 ['ab'] ))

       When state 1 is reached, it indicates that pattern 'a' has matched. Since
       all subsequent states are acceptance states the last acceptance does
       not have to be stored. The only way that 'a' is detected is on drop
       out from state 1 (see drop-out handling).

       Note, that this is equally true, if the acceptance state transits 
       on itself.
    """
    assert isinstance(State, state_machine.State)
    assert SM.__class__.__name__ == "StateMachine"
    assert State.is_acceptance()

    reachable_state_list = State.transitions().get_target_state_index_list()

    for state_index in reachable_state_list:
        state = SM.states[state_index]

        if state.is_acceptance() == False: return True
        # Is there at least one origin that is unconditioned? If not,
        # the trailing last acceptance must be stored.
        for origin in state.origins().get_list():
            if   not origin.is_acceptance():                      continue
            elif origin.pre_context_begin_of_line_f():            continue
            elif origin.pre_context_id() != -1L:                  continue
            elif origin.pseudo_ambiguous_post_context_id() != -1: continue
            else:
                # We found an un-conditioned acceptance state.
                # => State is 'OK' (There will be an acceptance that 
                # overwrites the acceptance of the current one)
                break
                # (Post conditioned states store only the input position,
                #  but are not acceptance states)
        else:
            # No un-conditioned acceptance origin found 
            # => State must be treated as if it was non-acceptance
            return True

    return False



