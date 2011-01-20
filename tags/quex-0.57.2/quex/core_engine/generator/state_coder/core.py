from   quex.core_engine.state_machine.core         import State 
import quex.core_engine.generator.languages.core   as languages
from   quex.core_engine.generator.languages.core   import __nice
import quex.core_engine.generator.state_coder.input_block      as input_block
import quex.core_engine.generator.state_coder.transition_block as transition_block
import quex.core_engine.generator.state_coder.transition       as transition
import quex.core_engine.generator.state_coder.acceptance_info  as acceptance_info
import quex.core_engine.generator.state_coder.drop_out         as drop_out
from   quex.input.setup                                        import setup as Setup
from copy import deepcopy


def do(state, StateIdx, SMD=False):
    """Produces code for all state transitions. Programming language is determined
       by 'Language'.
    """    
    assert isinstance(state, State)
    assert SMD.__class__.__name__   == "StateMachineDecorator"
    assert len(state.transitions().get_epsilon_target_state_index_list()) == 0, \
           "Epsilon transition contained target states: state machine was not made a DFA!\n" + \
           "Epsilon target states = " + repr(state.transitions().get_epsilon_target_state_index_list())
    InitStateF = StateIdx == SMD.sm().init_state_index

    LanguageDB = Setup.language_db

    prolog = ""
    if not InitStateF: 
        prolog += "    __quex_assert(false); /* No drop-through between states */\n"

    # Special handling of dead-end-states, i.e. states with no further transitions.
    dead_end_state_info = SMD.dead_end_state_db().get(StateIdx)
    if dead_end_state_info != None:
        txt = transition.do_dead_end_state_stub(dead_end_state_info, SMD)
        # Some states do not need 'stubs' to terminal since they are straight
        # forward transitions to the terminal.
        if len(txt) == 0: return []
        prolog += LanguageDB["$label-def"]("$entry-stub", StateIdx)
        txt.insert(0, prolog)
        return txt

    prolog += LanguageDB["$label-def"]("$entry", StateIdx)

    TriggerMap = state.transitions().get_trigger_map()
    assert TriggerMap != []  # Only dead end states have empty trigger maps.
    #                        # => Here, the trigger map cannot be empty.

    txt = \
          input_block.do(StateIdx, InitStateF, SMD)      + \
          acceptance_info.do(state, StateIdx, SMD)       + \
          transition_block.do(TriggerMap, StateIdx, SMD) + \
          drop_out.do(state, StateIdx, SMD)

    if InitStateF and SMD.forward_lexing_f():
        # Comment see: do_init_state_input_epilog() function
        input_block.do_init_state_input_epilog(txt, SMD)
    
    if len(txt) != 0: txt.insert(0, prolog)
    return txt 

