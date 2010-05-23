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
            return LanguageDB["$goto-template-target"](info.template_index, 
                                                       info.target_index)
        elif not info.uniform_state_entries_f():
            return LanguageDB["$goto-template-state-key"](info.template_index) 
        else:
            return LanguageDB["$goto"]("$entry", info.template_index)

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

    dead_end_target_state = DSM.dead_end_state_db()[TargetStateIdx]
    assert dead_end_target_state.is_acceptance(), \
           "NON-ACCEPTANCE dead end detected during code generation!\n" + \
           "A dead end that is not deleted must be an ACCEPTANCE dead end. See\n" + \
           "state_machine.dead_end_analyzis.py and generator.state_machine_coder.py.\n" + \
           "If this is not the case, then something serious went wrong. A transition\n" + \
           "to a non-acceptance dead end is to be translated into a drop-out."

    if dead_end_target_state.origins().contains_any_pre_context_dependency(): 
        # Backward lexing (pre-condition or backward input position detection) cannot
        # depend on pre-conditions, since it is not part of the 'main' lexical analyser
        # process.
        assert DSM.mode() == "ForwardLexing"
        return LanguageDB["$goto"]("$entry", TargetStateIdx)   # router to terminal

    elif DSM.mode() == "ForwardLexing":
        winner_origin = dead_end_target_state.origins().find_first_acceptance_origin()
        assert type(winner_origin) != type(None)               # see first assert in this block

        terminal_id = winner_origin.state_machine_id

        # During forward lexing (main lexer process) there are dedicated terminal states.
        return __goto_distinct_terminal(winner_origin)

    elif DSM.mode() == "BackwardLexing":
        # When checking a pre-condition no dedicated terminal exists. However, when
        # we check for pre-conditions, a pre-condition flag needs to be set.
        return "".join(acceptance_info.backward_lexing(dead_end_target_state.origins().get_list()))

    elif DSM.mode() == "BackwardInputPositionDetection":
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        txt  = [ LanguageDB["$input/decrement"], "\n"] + \
               acceptance_info.backward_lexing_find_core_pattern(dead_end_target_state.origins().get_list()) + \
               [ LanguageDB["$goto"]("$terminal-general-bw", True) ]  # general terminal
        return "".join(txt)

    else:
        assert False, "Impossible engine generation mode: '%s'" % DSM.mode()
    
def __goto_distinct_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return LanguageDB["$goto"]("$terminal", Origin.state_machine_id)
    else:
        return LanguageDB["$goto"]("$terminal-direct", Origin.state_machine_id)

def do_dead_end_router(state, StateIdx, BackwardLexingF):
    # DeadEndType == -1:
    #    States, that do not contain any acceptance transit to the 'General Terminal'
    #    They do not have to be coded. Instead the 'jump' must be redirected immediately
    #    to the general terminal.
    # DeadEndType == some integer:
    #    States, where the acceptance is clear must be redirected to the correspondent
    #    terminal given by the integer.
    # DeadEndType == None:
    #    States, where the acceptance depends on the run-time pre-conditions being fulfilled
    #    or not. They are the only ones, that are 'implemented' as routers, that map to
    #    a terminal correspondent the pre-conditions.
    assert isinstance(state, State)
    assert state.is_acceptance()
    LanguageDB = Setup.language_db

    if state.origins().contains_any_pre_context_dependency() == False: 
        return [] # LanguageDB["$goto-last_acceptance"] + "\n"

    txt = [ 
            acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                    __goto_distinct_terminal),
            # Pre-conditions might not have their pre-condition fulfilled.
            LanguageDB["$goto-last_acceptance"],
            "\n"
          ]

    return txt
