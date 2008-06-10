import quex.core_engine.generator.acceptance_info as acceptance_info

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
        
        if dead_end_target_state.is_acceptance() == False: 
            return LanguageDB["$goto"]("$terminal-general", BackwardLexingF)   # general terminal

        elif dead_end_target_state.origins().contains_any_pre_context_dependency(): 
            # Backward lexing (pre-condition or backward input position detection) cannot
            # depend on pre-conditions, since it is not part of the 'main' lexical analyser
            # process.
            assert not BackwardLexingF
            return LanguageDB["$goto"]("$entry", TargetStateIdx)               # router to terminal


        if not BackwardLexingF:
            winner_origin = dead_end_target_state.origins().find_first_acceptance_origin()
            assert type(winner_origin) != type(None) # see first condition in this block

            terminal_id = winner_origin.state_machine_id

            # During forward lexing (main lexer process) there are dedicated terminal states.
            if winner_origin.post_context_id() != -1:    
                # post conditions require to seek the last store acceptance position
                return LanguageDB["$goto"]("$terminal", terminal_id)                # direct terminal
            else:
                # 'normal' acceptances can transit directly to the terminal. they no not
                # seek an input position, because they are immediately at the right place.
                if BackwardLexingF: txt = LanguageDB["$input/decrement"] + "\n"
                else:               txt = LanguageDB["$input/increment"] + "\n"
                txt += LanguageDB["$goto"]("$terminal-without-seek", terminal_id)  # direct terminal
                return txt
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

    def __on_detection_code(StateMachineName, Origin):
        if Origin.post_context_id() != -1:
            return LanguageDB["$goto"]("$terminal", Origin.state_machine_id)
        else:
            if BackwardLexingF: txt = LanguageDB["$input/decrement"] + "\n"
            else:               txt = LanguageDB["$input/increment"] + "\n"
            txt += LanguageDB["$goto"]("$terminal-without-seek", Origin.state_machine_id)
            return txt

    txt = acceptance_info.get_acceptance_detector(State.origins().get_list(), 
                                                  __on_detection_code,
                                                  LanguageDB, StateMachineName)
            
    # -- double check for consistency
    assert txt != "", "Acceptance state without acceptance origins!"        

    return txt
