from   quex.core_engine.state_machine.core import State 
import quex.core_engine.generator.state_coder.acceptance_info as acceptance_info
from   quex.input.setup import setup as Setup
from   quex.core_engine.interval_handling import Interval

from math import log

def do(TargetStateIdx, CurrentStateIdx, TriggerInterval, SMD):
    LanguageDB = Setup.language_db

    # Indentation counting is something totally different ...
    result = __indentation_count_action(TargetStateIdx, SMD)
    if result != None: return result

    # Template Transition Targets are a little different ...
    result = __template_transition_target(TargetStateIdx, SMD)
    if result != None: return result

    # Tiny neighbour transitions that can be implemented by a switch
    # statement (assembler might likely convert this into 'indexing').
    # result = __tiny_neighbour_transitions(TargetStateIdx, CurrentStateIdx, SMD)
    # if result != None: return result

    # All normal transitions can be handled by 'goto' plus 'label'
    # (The init state (forward) does not increment the input position. Thus, here we
    #  need to transit to the position where the input position is incremented.)
    if SMD != None and TargetStateIdx == SMD.sm().init_state_index and SMD.forward_lexing_f():
        return LanguageDB["$goto"]("$input", TargetStateIdx)
    else:
        return LanguageDB["$goto-pure"](get_label(TargetStateIdx, CurrentStateIdx, TriggerInterval, SMD))

def __indentation_count_action(Info, SMD):
    """Indentation counters may count as a consequence of a 'triggering'."""
    if Info.__class__.__name__ != "IndentationCounter": return None

    # Spaces simply increment
    if Info.type == "space": 
        if Info.number != -1: add_str = "%i" % Info.number
        else:                 add_str = "me->" + Info.variable_name
        return "me->counter._indentation += %s;" % add_str
    
    # Grids lie on a grid:
    elif Info.type == "grid":
        if Info.number != -1: 
            log2 = log(Info.number)/log(2)
            if log2.is_integer():
                # For k = a potentials of 2, the expression 'x - x % k' can be written as: x & ~log2(mask) !
                # Thus: x = x - x % k + k = x & mask + k
                mask = (1 << int(log2)) - 1
                return "me->counter._indentation &= ~ ((QUEX_TYPE_INDENTATION)0x%X);\n" % mask + \
                       "me->counter._indentation += %i;\n" % Info.number
            else:
                add_str = "%i" % Info.number
        else:   
            add_str = "me->" + Info.variable_name

        return "me->counter._indentation = (me->counter._indentation - (me->counter._indentation %% %s)) + %s;" \
               % (add_str, add_str)

    elif Info.type == "bad":
        assert Info.number != -1
        return "goto INDENTATION_COUNTER_%i_BAD_CHARACTER;\n" % Info.number

    else:
        assert False, "Unreachable code has been reached."
    
def __template_transition_target(Info, SMD):
    """Template transition target states. The target state is determined at 
       run-time based on a 'state_key' for the template.
       NOTE: This handles also the recursive case.
    """
    LanguageDB = Setup.language_db
    if Info.__class__.__name__ != "TemplateTarget": return None

    if not Info.recursive():
        if SMD.forward_lexing_f(): cmd = "$goto-template-target"
        else:                      cmd = "$goto-template-target-bw" 
        return LanguageDB[cmd](Info.template_index, Info.target_index)

    elif not Info.uniform_state_entries_f():
        if SMD.forward_lexing_f(): cmd = "$goto-template-state-key"
        else:                      cmd = "$goto-template-state-key-bw"
        return LanguageDB[cmd](Info.template_index) 

    else:
        return LanguageDB["$goto"]("$template", Info.template_index)

def get_label(TargetStateIdx, CurrentStateIdx, TriggerInterval, SMD):
    """
        TargetStateIdx: != None: Index of the state to which 'goto' has to go.
                        == None: Drop Out. Goto a terminal state.

        SMD == None: We are not concerned with the whole state machine and just want to
                     create a nice binary-bracketing transition (e.g. for range skippers).
    """
    LanguageDB = Setup.language_db

    assert TargetStateIdx.__class__.__name__ != "TemplateTarget" 
    # TargetStateIdx == None --> drop out
    # TargetStateIdx == -1   --> buffer limit code; reload required
    assert    TargetStateIdx                 == None \
           or TargetStateIdx                 == -1   \
           or TargetStateIdx                 >= 0

    assert    CurrentStateIdx == None \
           or CurrentStateIdx >= 0

    assert    SMD                    == None \
           or SMD.__class__.__name__ == "StateMachineDecorator"

    assert    TriggerInterval                    == None       \
           or TriggerInterval.__class__.__name__ == "Interval" \

    if SMD != None and SMD.dead_end_state_db().has_key(TargetStateIdx):
        # (0) Transitions to 'dead-end-state'
        return __dead_end_state_label(TargetStateIdx, SMD)

    elif TargetStateIdx == None:   
        # (1) Drop Out
        #     The current interval does not contain the buffer limit
        #     code (Otherwise, TargetStateIdx == -1). 
        #     Thus, no reload is required.
        return LanguageDB["$label"]("$drop-out-direct", CurrentStateIdx)

    elif TargetStateIdx == -1:
        # (2) 'Target == -1' => buffer limit code; reload required
        assert TriggerInterval.size() == 1
        assert TriggerInterval.contains(Setup.buffer_limit_code)
        return LanguageDB["$label"]("$reload", CurrentStateIdx)

    else:
        # (3) The very normal transition to another state
        assert type(TargetStateIdx) in [int, long]
        return LanguageDB["$label"]("$entry", TargetStateIdx)

def __dead_end_state_label(TargetStateIdx, SMD):
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
            return __label_distinct_terminal(winner_origin_list[0])

        else:
            # Pre-context dependency can only appear in forward lexing which is the analyzis
            # that determines the winning pattern. BackwardInputPositionDetection and 
            # BackwardLexing can never depend on pre-conditions.
            return LanguageDB["$label"]("$entry-stub", TargetStateIdx)   # router to terminal

    elif SMD.backward_lexing_f():
        return LanguageDB["$label"]("$entry-stub", TargetStateIdx)   # router to terminal

    elif SMD. backward_input_position_detection_f():
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return LanguageDB["$label"]("$entry-stub", TargetStateIdx)   # router to terminal

    else:
        assert False, "Impossible engine generation mode: '%s'" % SMD.mode()
    
def do_dead_end_state_stub(DeadEndStateInfo, SMD):
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

    if SMD.forward_lexing_f():
        if not pre_context_dependency_f:
            assert len(winner_origin_list) == 1
            # Direct transition to terminal possible, no stub required.
            return [] 

        else:
            return [ acceptance_info.get_acceptance_detector(state.origins().get_list(), 
                                                             __goto_distinct_terminal),
                    "\n" ]

    elif SMD.backward_lexing_f():
        # When checking a pre-condition no dedicated terminal exists. However, when
        # we check for pre-conditions, a pre-condition flag needs to be set.
        return acceptance_info.backward_lexing(state.origins().get_list()) + \
               [ LanguageDB["$goto"]("$terminal-general-bw", True) ] 


    elif SMD.backward_input_position_detection_f():
        # When searching backwards for the end of the core pattern, and one reaches
        # a dead end state, then no position needs to be stored extra since it was
        # stored at the entry of the state.
        return [ LanguageDB["$input/decrement"], "\n"] + \
               acceptance_info.backward_lexing_find_core_pattern(state.origins().get_list()) + \
               [ LanguageDB["$goto"]("$terminal-general-bw", True) ]

    assert False, \
           "Unknown mode '%s' in terminal stub code generation." % Mode

def __label_distinct_terminal(Origin):
    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == -1:
        return LanguageDB["$label"]("$terminal", Origin.state_machine_id)
    else:
        return LanguageDB["$label"]("$terminal-direct", Origin.state_machine_id)

def __goto_distinct_terminal(Origin):

    # No unconditional case of acceptance 
    if type(Origin) == type(None): 
        LanguageDB = Setup.language_db
        return LanguageDB["$goto-last_acceptance"]

    assert Origin.is_acceptance()
    LanguageDB = Setup.language_db
    return LanguageDB["$goto-pure"](__label_distinct_terminal(Origin))

