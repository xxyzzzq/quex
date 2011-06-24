import quex.engine.generator.state_coder2.core   as     state_coder
from   quex.engine.analyzer.core                 import Analyzer
from   quex.blackboard                           import EngineTypes
from   quex.input.setup                          import setup as Setup
# import quex.engine.generator.template_coder  as template_coder
# import quex.engine.generator.paths_coder     as paths_coder

def do(RawSM, EngineType):
    """Generate source code for a given state machine 'SM'.
    """
    assert isinstance(RawSM, quex.engine.state_machine.core.StateMachine)
    assert isinstance(EngineType, EngineTypes)

    LanguageDB = Setup.language_db

    analyzer   = Analyzer(RawSM, EngineType)

    # Track what states are treated with different methods (see below)
    remainder  = set(analyzer.state_db.keys())

    # (*) Init State
    init_state = state_coder.do(analyzer.state_db[analyzer.init_state_index])
    remainder.discard(analyzer.init_state_index)

    # (*) [Optional] Path-Compressed States
    path_compressed_states = []
    # if Setup.compression_path_f or Setup.compression_path_uniform_f:
    #    path_compressed_states, state_index_set = paths_coder.do(analyzer, Setup.compression_path_uniform_f)
    #    remainder.difference_update(state_index_set)
    
    # (*) [Optional] Template-Compressed States
    template_compressed_states = []
    # if Setup.compression_template_f:
    #    template_compressed_states, state_index_set = template_coder.do(analyzer, Setup.compression_template_coef)
    #    remainder.difference_update(state_index_set)
    
    # (*) All other (normal) states
    normal_states = [ state_coder.do(state) for state in get_sorted_state_list(analyzer.state_db, remainder)]

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

