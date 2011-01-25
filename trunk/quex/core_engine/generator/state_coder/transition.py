from quex.input.setup import setup as Setup

def do(TargetInfo, CurrentStateIdx, SMD):
    LanguageDB = Setup.language_db

    # (*) Indentation counting, may be?
    #
    if   TargetInfo.__class__.__name__ == "IndentationCounter": 
        return __indentation_count_action(TargetInfo, SMD)

    # (*) Template Transition Targets, may be?
    #
    elif TargetInfo.__class__.__name__ == "TemplateTarget": 
        return __template_transition_target(TargetInfo, SMD)

    # (*) Normal Transitions: goto + label
    #
    elif TargetInfo == None:
        return get_transition_to_drop_out(CurrentStateIdx, ReloadF=False)

    elif TargetInfo == -1:
        return get_transition_to_drop_out(CurrentStateIdx, ReloadF=True)

    else:
        return get_transition_to_state(TargetInfo, SMD)

def get_transition_to_state(TargetInfo, SMD):
    LanguageDB = Setup.language_db
    if SMD != None:
        if TargetInfo == SMD.sm().init_state_index and SMD.forward_lexing_f():
            # The init state (forward) does not increment the input position. Thus, here we
            # need to transit to the position where the input position is incremented.
            return LanguageDB["$goto"]("$input", SMD.sm().init_state_index)

        elif type(TargetInfo) in [int, long] and SMD.dead_end_state_db().has_key(TargetInfo):
            return __get_transition_to_dead_end_state(TargetInfo, SMD)

    return LanguageDB["$goto-pure"](get_label_of_state(TargetInfo, SMD))

def get_transition_to_drop_out(CurrentStateIdx, ReloadF):
    LanguageDB = Setup.language_db
    return LanguageDB["$goto-pure"](get_label_of_drop_out(CurrentStateIdx, ReloadF))

def get_transition_to_terminal(Origin):
    # No unconditional case of acceptance 
    if type(Origin) == type(None): 
        LanguageDB = Setup.language_db
        return LanguageDB["$goto-last_acceptance"]

    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    return LanguageDB["$goto-pure"](get_label_of_terminal(Origin))

def __get_transition_to_dead_end_state(TargetStateIndex, SMD):
    LanguageDB = Setup.language_db
    return LanguageDB["$goto-pure"](__get_label_of_dead_end_state(TargetStateIndex, SMD))

def get_label_of_state(TargetStateIdx, SMD):
    LanguageDB = Setup.language_db

    if SMD != None and SMD.dead_end_state_db().has_key(TargetStateIdx):
        # Transitions to 'dead-end-state'
        return  __get_label_of_dead_end_state(TargetStateIdx, SMD)
    else:
        # The very normal transition to another state
        return LanguageDB["$label"]("$entry", TargetStateIdx)

def get_label_of_drop_out(CurrentStateIdx, ReloadF=False):
    LanguageDB = Setup.language_db

    if not ReloadF: 
        # Drop Out
        # The current interval does not contain the buffer limit
        # code (Otherwise, TargetStateIdx == -1). 
        # Thus, no reload is required.
        return LanguageDB["$label"]("$drop-out-direct", CurrentStateIdx)

    else:
        # 'Target == -1' => buffer limit code; reload required
        return LanguageDB["$label"]("$reload", CurrentStateIdx)

def get_label_of_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return LanguageDB["$label"]("$terminal", Origin.state_machine_id)
    else:
        return LanguageDB["$label"]("$terminal-direct", Origin.state_machine_id)

def __get_label_of_dead_end_state(TargetStateIdx, SMD):
    """The TargetStateIdx is mentioned to be a dead-end-state! That means, that
       there is actually no 'transition block' in that state and it transits
       directly to a terminal.  The jump to those states can be shortcut. It is
       not necessary to go to that state and then drop out, and then goto the
       terminal. The transition to the terminal can be done directly.  
    """
    assert SMD != None
    LanguageDB = Setup.language_db

    pre_context_dependency_f, \
    winner_origin_list,       \
    dead_end_target_state     = SMD.dead_end_state_db()[TargetStateIdx]

    assert dead_end_target_state.is_acceptance(), \
           "NON-ACCEPTANCE dead end detected during code generation!\n" + \
           "A dead end that is not deleted must be an ACCEPTANCE dead end. See\n" + \
           "state_machine.dead_end_analyzis.py and generator.state_machine_coder.py.\n" + \
           "If this is not the case, then something serious went wrong. A transition\n" + \
           "to a non-acceptance dead end is to be translated into a drop-out."

    if SMD.forward_lexing_f():
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # During forward lexing (main lexer process) there are dedicated terminal states.
            return get_label_of_terminal(winner_origin_list[0])

        else:
            # Pre-context dependency can only appear in forward lexing which is the analyzis
            # that determines the winning pattern. BackwardInputPositionDetection and 
            # BackwardLexing can never depend on pre-conditions.
            return LanguageDB["$label"]("$entry-stub", TargetStateIdx)   # router to terminal

    elif SMD.backward_lexing_f():
        return LanguageDB["$label"]("$entry-stub", TargetStateIdx)       # router to terminal

    elif SMD.backward_input_position_detection_f():
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return LanguageDB["$label"]("$entry-stub", TargetStateIdx)       # router to terminal

    else:
        assert False, "Impossible engine generation mode: '%s'" % SMD.mode()

