from   quex.engine.generator.state_machine_decorator import StateMachineDecorator

import quex.engine.generator.state_coder.core as state_coder
import quex.engine.generator.template_coder   as template_coder
import quex.engine.generator.paths_coder      as paths_coder
from   quex.input.setup                       import setup as Setup

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
    
    # Track what states are treated with different methods
    remainder = set(state_machine.states.keys())

    # (*) Init State
    init_state = state_coder.do(state_machine.states[state_machine.init_state_index], 
                                state_machine.init_state_index, 
                                SMD)
    remainder.discard(state_machine.init_state_index)

    # (*) [Optional] Path-Compressed States
    path_compressed_states = []
    if Setup.compression_path_f or Setup.compression_path_uniform_f:
        path_compressed_states, state_index_set = paths_coder.do(SMD, Setup.compression_path_uniform_f)
        remainder.difference_update(state_index_set)
    
    # (*) [Optional] Template-Compressed States
    template_compressed_states = []
    if Setup.compression_template_f:
        template_compressed_states, state_index_set = template_coder.do(SMD, Setup.compression_template_coef)
        remainder.difference_update(state_index_set)
    
    # (*) All other (normal) states
    normal_states = []
    for state_index, state in get_sorted_state_list(state_machine.states, remainder):
        normal_states.extend(state_coder.do(state, state_index, SMD))

    return init_state + \
           normal_states + \
           path_compressed_states + \
           template_compressed_states 

def get_sorted_state_list(StateDict, RemainderStateIndexList):
    """Sort the list in a away, so that states that are used more
       often appear earlier. This happens in the hope of more 
       cache locality. 
    """
    # Count number of transitions to a state: frequency_db
    frequency_db = {}
    for state in StateDict.itervalues():
        for target_index in state.transitions().get_map().iterkeys():
            if frequency_db.has_key(target_index): frequency_db[target_index] += 1
            else:                                  frequency_db[target_index]  = 1

    # Only list states that remain to be coded.
    state_list = []
    for index, state in StateDict.iteritems():
        if index not in RemainderStateIndexList: continue
        state_list.append((index, state))

    # x[0]               -- state index; 
    # frequency_db[x[0]] -- frequency that state 'state_index' is entered.
    state_list.sort(key=lambda x: frequency_db[x[0]], reverse=True)
    return state_list

