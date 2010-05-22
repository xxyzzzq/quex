from copy import deepcopy

from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.languages.core   as languages
from   quex.core_engine.generator.languages.core   import __nice
import quex.core_engine.generator.state_coder.core as state_coder
import quex.core_engine.generator.template_coder   as template_coder
from   quex.input.setup import setup as Setup


def do(SMD):
    """Returns the program code implementing the StateMachine's behavior.
       NOTE: This function should only be called on a DFA after the call
             to 'filter_dominated_origins'. The latter is important
             to ensure that for an acceptance state there is only one
             related original state.

       The procedure for each state is the following:
            i)  input <-- next character from stream 
            ii) state transition code (include marking of last success state
                and last success stream position).                  
    """
    assert isinstance(SMD, StateMachineDecorator)
    LanguageDB = Setup.language_db

    state_machine = SMD.sm()
    
    txt = []
    prolog = ""

    # -- treat initial state separately 
    if state_machine.is_init_state_a_target_state():
        # (only define the init state label, if it is really needed)
        txt.extend([LanguageDB["$label-def"]("$entry", state_machine.init_state_index), "\n"])

    init_state = state_machine.states[state_machine.init_state_index]
    #
    # NOTE: Only the init state provides a transition via 'EndOfFile'! In any other
    #       case, end of file needs to cause a drop out! After the drop out, lexing
    #       starts at furthest right before the EndOfFile and the init state transits
    #       into the TERMINAL_END_OF_FILE.
    txt.extend(state_coder.do(init_state, 
                              state_machine.init_state_index, 
                              SMD, InitStateF = True))

    # -- Code for templated states [Optional]
    #    (those states do not have to be coded later)
    templated_state_index_list = set([])
    if Setup.compression_template_f:
        code, template_prolog, templated_state_index_list = \
                template_coder.do(SMD, Setup.compression_template_coef)
        txt.append(code)
        prolog += template_prolog
        
    # -- all other states
    for state_index, state in state_machine.states.items():

        # the init state has been coded already
        if state_index == state_machine.init_state_index: continue
        elif state_index in templated_state_index_list:   
            continue

        txt.append("    __quex_assert(false); /* No drop-through between states */\n")
        state_code = state_coder.do(state, state_index, SMD)

        # some states are not coded (some dead end states)
        if len(state_code) == 0: continue

        txt.append("\n")
        txt.extend(state_code)
        txt.append("\n")
    
    return "".join(txt), prolog





