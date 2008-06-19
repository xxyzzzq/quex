import quex.core_engine.generator.acceptance_info as acceptance_info
from   quex.input.setup import setup as Setup


def __goto_distinct_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    if Origin.post_context_id() != -1:
        # The seek for the end of the core pattern is part of the 'normal' terminal
        # if the terminal 'is' a post conditioned pattern acceptance.
        return LanguageDB["$goto"]("$terminal", Origin.state_machine_id)
    else:
        return LanguageDB["$goto"]("$terminal-with-preparation", Origin.state_machine_id)


def do(StateMachineName, CurrentStateIdx, TargetStateIdx, 
       BackwardLexingF, BackwardInputPositionDetectionF, 
       DeadEndStateDB, LanguageDB):
    """
        StateMachineName: Name of the state machine.

        TargetStateIdx: != None: Index of the state to which 'goto' has to go.
                        == None: Drop Out. Goto a terminal state.

        BackwardLexingF: Flag indicating wether this function is called during 
                         normal forward lexing, or for the implementation of a 
                         backwards state machine (complex pre-conditions).

        DeadEndStateDB: Contains information about states that have no further transitions. 
                        If a transition to such a state has to happen, on can directly
                        go to a correspondent terminal.
                        
    """
    assert type(DeadEndStateDB) == dict
    assert TargetStateIdx == None or TargetStateIdx >= 0

    if DeadEndStateDB.has_key(TargetStateIdx):
        dead_end_target_state = DeadEndStateDB[TargetStateIdx]
        assert dead_end_target_state.is_acceptance(), \
               "NON-ACCEPTANCE dead end detected during code generation!\n" + \
               "A dead end that is not deleted must be an ACCEPTANCE dead end. See\n" + \
               "state_machine.dead_end_analysis.py and generator.state_machine_coder.py.\n" + \
               "If this is not the case, then something serious went wrong."

        if dead_end_target_state.origins().contains_any_pre_context_dependency(): 
            # Backward lexing (pre-condition or backward input position detection) cannot
            # depend on pre-conditions, since it is not part of the 'main' lexical analyser
            # process.
            assert not BackwardLexingF
            return LanguageDB["$goto"]("$entry", TargetStateIdx)       # router to terminal

        elif not BackwardLexingF:
            winner_origin = dead_end_target_state.origins().find_first_acceptance_origin()
            assert type(winner_origin) != type(None) # see first condition in this block

            terminal_id = winner_origin.state_machine_id

            # During forward lexing (main lexer process) there are dedicated terminal states.
            return __goto_distinct_terminal(winner_origin)

        else:
            txt = ""
            if not BackwardInputPositionDetectionF:
                # When checking a pre-condition no dedicated terminal exists. However, when
                # we check for pre-conditions, a pre-condition flag needs to be set.
                txt += acceptance_info.backward_lexing(dead_end_target_state.origins().get_list(), 
                                                       LanguageDB)
            else:
                # When searching backwards for the end of the core pattern, and one reaches
                # a dead end state, then no position needs to be stored extra since it was
                # stored at the entry of the state.
                txt += LanguageDB["$input/decrement"] + "\n"
                txt += acceptance_info.backward_lexing_find_core_pattern(dead_end_target_state.origins().get_list(), 
                                                                         LanguageDB)

            txt += LanguageDB["$goto"]("$terminal-general", True)   # general terminal
            return txt
    
    # (*) A very normal transition to another state (maybe also a drop-out)
    if   TargetStateIdx == None:   
        return LanguageDB["$goto"]("$drop-out", CurrentStateIdx) + "\n"
    else:
        return LanguageDB["$goto"]("$entry", TargetStateIdx) + "\n"
    

def do_dead_end_router(State, StateIdx, StateMachineName,  BackwardLexingF, LanguageDB):
    # DeadEndType == -1:
    #    States, that do not contain any acceptance transit to the 'General Terminal'
    #    The do not have to be coded. Instead the 'jump' must be redirected immediately
    #    to the general terminal.
    # DeadEndType == some integer:
    #    States, where the acceptance is clear must be redirected to the correspondent
    #    terminal given by the integer.
    # DeadEndType == None:
    #    States, where the acceptance depends on the run-time pre-conditions being fulfilled
    #    or not. They are the only once, that are 'implemented' as routers, that map to
    #    a terminal correspondent the pre-conditions.
    if State.origins().contains_any_pre_context_dependency() == False: 
        return ""

    txt = acceptance_info.get_acceptance_detector(State.origins().get_list(), 
                                                  __goto_distinct_terminal,
                                                  LanguageDB, StateMachineName)
            
    # -- double check for consistency
    assert txt != "", "Acceptance state without acceptance origins!"        

    return txt
