from copy import deepcopy

from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.languages.core   as languages
from   quex.core_engine.generator.languages.core   import __nice
import quex.core_engine.generator.state_coder.core as state_coder
import quex.core_engine.generator.template_coder   as template_coder
import quex.core_engine.generator.paths_coder      as paths_coder
from   quex.input.setup import setup as Setup


def do(SMD, TemplateHasBeenCodedBeforeF=False):
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
    
    txt                  = []
    done_state_index_set = set([])
    local_variable_db    = {}

    init_state = state_machine.states[state_machine.init_state_index]
    # NOTE: Only the init state provides a transition via 'EndOfFile'! In any other
    #       case, end of file needs to cause a drop out! After the drop out, lexing
    #       starts at furthest right before the EndOfFile and the init state transits
    #       into the TERMINAL_END_OF_FILE.
    #       (state_coder identifies the 'init_state' by its own, no need mentioning)
    txt.extend(state_coder.do(init_state, state_machine.init_state_index, SMD))

    # -- Coding path states [Optional]
    if Setup.compression_path_f or Setup.compression_path_uniform_f:
        code, variable_db, state_index_set = \
                paths_coder.do(SMD, Setup.compression_path_uniform_f)
        done_state_index_set.update(state_index_set)
        txt.append(code)
        local_variable_db.update(variable_db)
    
    # -- Coding templated states [Optional]
    #    (those states do not have to be coded later)
    if Setup.compression_template_f:
        code, variable_db, state_index_set = \
                template_coder.do(SMD, Setup.compression_template_coef)
        done_state_index_set.update(state_index_set)
        txt.append(code)
        local_variable_db.update(variable_db)
        
    # -- all other states
    for state_index, state in state_machine.states.items():

        # the init state has been coded already
        if state_index == state_machine.init_state_index: continue
        elif state_index in done_state_index_set:   
            continue
        state_code = state_coder.do(state, state_index, SMD)

        # some states are not coded (some dead end states)
        if len(state_code) == 0: continue

        txt.append("\n")
        txt.extend(state_code)
        txt.append("\n")
    
    return "".join(txt), local_variable_db





