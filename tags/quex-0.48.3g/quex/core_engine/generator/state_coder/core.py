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

    label_str = LanguageDB["$label-def"]("$entry", StateIdx)
    if not InitStateF:
        label_str = "    __quex_assert(false); /* No drop-through between states */\n" + \
                    label_str

    # Special handling of dead-end-states, i.e. states with no further transitions.
    if SMD.dead_end_state_db().has_key(StateIdx):
        txt = transition.do_dead_end_router(state, StateIdx, SMD.backward_lexing_f())
        if len(txt) != 0: txt.insert(0, label_str)
        return txt

    TriggerMap = state.transitions().get_trigger_map()
    assert TriggerMap != []  # Only dead end states have empty trigger maps.
    #                        # => Here, the trigger map cannot be empty.

    txt = \
          input_block.do(StateIdx, InitStateF, SMD.backward_lexing_f())  + \
          acceptance_info.do(state, StateIdx, SMD)                       + \
          transition_block.do(TriggerMap, StateIdx, InitStateF, SMD)     + \
          drop_out.do(state, StateIdx, SMD, InitStateF)

    if InitStateF and not SMD.backward_lexing_f():
        # Define the transition entry of the init state **after** the init state itself.
        # It contains 'increment input pointer', which is not required at the begin of
        # a lexical analyzis--in forward lexing. When other states transit to the init
        # state, they need to increase the input pointer. 
        # All this is not necessary in backward lexing, since there, the init state's
        # original entry contains 'decrement input pointer' anyway.
        txt.extend([        LanguageDB["$label-def"]("$input", StateIdx),
                    "    ", LanguageDB["$input/increment"],          "\n",
                    "    ", LanguageDB["$goto"]("$entry", StateIdx), "\n"])
    
    if len(txt) != 0: txt.insert(0, label_str)
    return txt # .replace("\n", "\n    ") + "\n"

