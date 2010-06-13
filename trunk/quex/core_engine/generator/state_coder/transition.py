from   quex.core_engine.state_machine.core import State 
import quex.core_engine.generator.state_coder.acceptance_info as acceptance_info
from   quex.input.setup import setup as Setup

def do(TargetStateIdx, CurrentStateIdx, TriggerInterval, DSM):
    """
        TargetStateIdx: != None: Index of the state to which 'goto' has to go.
                        == None: Drop Out. Goto a terminal state.

        DSM == None: We are not concerned with the whole state machine and just want to
                     create a nice binary-bracketing transition (e.g. for range skippers).
    """
    LanguageDB = Setup.language_db

    assert    TargetStateIdx                    == None             \
           or TargetStateIdx.__class__.__name__ == "TemplateTarget" \
           or TargetStateIdx                    >= 0

    assert    CurrentStateIdx == None \
           or CurrentStateIdx >= 0

    assert    DSM                    == None \
           or DSM.__class__.__name__ == "StateMachineDecorator"

    assert    TriggerInterval                    == None       \
           or TriggerInterval.__class__.__name__ == "Interval" \

    # (0) Transitions to 'dead-end-state'
    if DSM != None and DSM.dead_end_state_db().has_key(TargetStateIdx):
        return __transition_to_dead_end_state(TargetStateIdx, DSM)

    # (1) Template transition target states. 
    #     The target state is determined at run-time based on a 'state_key'
    #     for the template.
    #     NOTE: This handles also the recursive case, if .target_index == -2
    if TargetStateIdx.__class__.__name__ == "TemplateTarget":
        info = TargetStateIdx
        if not info.recursive():
            if DSM.backward_lexing_f(): cmd = "$goto-template-target-bw"
            else:                       cmd = "$goto-template-target"
            return LanguageDB[cmd](info.template_index, info.target_index)

        elif not info.uniform_state_entries_f():
            if DSM.backward_lexing_f(): cmd = "$goto-template-state-key-bw"
            else:                       cmd = "$goto-template-state-key"
            return LanguageDB[cmd](info.template_index) 
        else:
            return LanguageDB["$goto"]("$template", info.template_index)

    # (2) The very normal transition to another state
    elif TargetStateIdx != None:   
        return LanguageDB["$goto"]("$entry", TargetStateIdx)

    # (3) Drop Out
    else:
        # The normal drop out contains a check against the buffer limit code.
        # This check can be avoided, if one is sure that the current interval
        # does not contain a buffer limit code.
        assert isinstance(Setup.buffer_limit_code, int)
        if    TriggerInterval == None \
           or TriggerInterval.contains(Setup.buffer_limit_code):
            return LanguageDB["$goto"]("$drop-out", CurrentStateIdx)
        else:
            return LanguageDB["$goto"]("$drop-out-direct", CurrentStateIdx)

def __transition_to_dead_end_state(TargetStateIdx, DSM):
    """The TargetStateIdx is mentioned to be a dead-end-state! That means, that
       there is actually no 'transition block' in that state and it transits
       directly to a terminal.  The jump to those states can be shortcut. It is
       not necessary to go to that state and then drop out, and then goto the
       terminal. The transition to the terminal can be done directly.  
    """
    LanguageDB = Setup.language_db
    assert DSM != None

    pre_context_dependency_f, \
    winner_origin_list,       \
    dead_end_target_state     = DSM.dead_end_state_db()[TargetStateIdx]

    assert dead_end_target_state.is_acceptance(), \
           "NON-ACCEPTANCE dead end detected during code generation!\n" + \
           "A dead end that is not deleted must be an ACCEPTANCE dead end. See\n" + \
           "state_machine.dead_end_analyzis.py and generator.state_machine_coder.py.\n" + \
           "If this is not the case, then something serious went wrong. A transition\n" + \
           "to a non-acceptance dead end is to be translated into a drop-out."

    if DSM.mode() == "ForwardLexing":
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # During forward lexing (main lexer process) there are dedicated terminal states.
            return __goto_distinct_terminal(winner_origin_list[0])

        else:
            # Pre-context dependency can only appear in forward lexing which is the analyzis
            # that determines the winning pattern. BackwardInputPositionDetection and 
            # BackwardLexing can never depend on pre-conditions.
            return LanguageDB["$goto"]("$entry-stub", TargetStateIdx)   # router to terminal

    elif DSM.mode() == "BackwardLexing":
        return LanguageDB["$goto"]("$entry-stub", TargetStateIdx)   # router to terminal

    elif DSM.mode() == "BackwardInputPositionDetection":
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return LanguageDB["$goto"]("$entry-stub", TargetStateIdx)   # router to terminal

    else:
        assert False, "Impossible engine generation mode: '%s'" % DSM.mode()
    
def do_dead_end_state_stub(DeadEndStateInfo, Mode):
    """Dead end states are states which are void of any transitions. They 
       all drop out to some terminal (or drop out totally). Many transitions 
       to goto states can be replaced by direct transitions to the correspondent
       terminal. Some dead end states, though, need to be replaced by 'stubs'
       where some basic handling is necessary. The implementation of such 
       stubs is handled inside this function.
    """
    LanguageDB = Setup.language_db

    pre_context_dependency_f, \
    winner_origin_list,       \
    state                     = DeadEndStateInfo

    assert isinstance(state, State)
    assert state.is_acceptance()

    if Mode == "ForwardLexing":
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # Direct transition to terminal possible, no stub required.
            return [] 

        else:
            return [ 
                    acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                            __goto_distinct_terminal),
                    # Pre-conditions might not have their pre-condition fulfilled.
                    LanguageDB["$goto-last_acceptance"],
                    "\n"
                   ]

    elif Mode == "BackwardLexing":
        # When checking a pre-condition no dedicated terminal exists. However, when
        # we check for pre-conditions, a pre-condition flag needs to be set.
        return acceptance_info.backward_lexing(state.origins().get_list())


    elif Mode == "BackwardInputPositionDetection":
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return [ LanguageDB["$input/decrement"], "\n"] + \
               acceptance_info.backward_lexing_find_core_pattern(state.origins().get_list()) + \
               [ LanguageDB["$goto"]("$terminal-general-bw", True) ]  # general terminal

    assert False, \
           "Unknown mode '%s' in terminal stub code generation." % Mode

def __goto_distinct_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return LanguageDB["$goto"]("$terminal", Origin.state_machine_id)
    else:
        return LanguageDB["$goto"]("$terminal-direct", Origin.state_machine_id)

