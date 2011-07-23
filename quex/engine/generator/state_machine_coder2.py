import quex.engine.generator.state_coder2.core   as     state_coder
from   quex.engine.analyzer.core                 import Analyzer
from   quex.engine.state_machine.core            import StateMachine
from   quex.engine.state_machine.state_core_info import EngineTypes
from   quex.blackboard                           import setup as Setup
# import quex.engine.generator.template_coder as template_coder
# import quex.engine.generator.paths_coder    as paths_coder

from   collections import defaultdict
from   itertools   import ifilter

def do(RawSM, EngineType):
    """Generate source code for a given state machine 'SM'.
    """
    assert isinstance(RawSM, StateMachine)
    assert EngineType in EngineTypes

    txt = []

    LanguageDB = Setup.language_db

    analyzer   = Analyzer(RawSM, EngineType)

    # Track what states are treated with different methods (see below)
    remainder  = set(analyzer.state_db.keys())

    # (*) Init State
    init_state = state_coder.do(txt, analyzer.state_db[analyzer.init_state_index], analyzer)
    remainder.discard(analyzer.init_state_index)

    # (*) [Optional] Path-Compressed States
    path_compressed_states = []
    if Setup.compression_path_f or Setup.compression_path_uniform_f:
        assert False # We cannot deal with that yet
    #    path_compressed_states, state_index_set = paths_coder.do(analyzer, Setup.compression_path_uniform_f)
    #    remainder.difference_update(state_index_set)
    
    # (*) [Optional] Template-Compressed States
    template_compressed_states = []
    if Setup.compression_template_f:
        assert False # We cannot deal with that yet
    #    template_compressed_states, state_index_set = template_coder.do(analyzer, Setup.compression_template_coef)
    #    remainder.difference_update(state_index_set)
    
    # (*) All other (normal) states (sorted by their frequency of appearance
    frequency_db = get_frequency_db(analyzer.state_db, remainder)
    for state in sorted(ifilter(lambda x: x.index in remainder, analyzer.state_db.itervalues()), 
                        key=lambda x: frequency_db[x.index], reverse=True):
        state_coder.do(txt, state, analyzer) 

    return txt

def get_frequency_db(StateDict, RemainderStateIndexList):
    """Sort the list in a away, so that states that are used more
       often appear earlier. This happens in the hope of more 
       cache locality. 
    """
    # Count number of transitions to a state: frequency_db
    frequency_db = defaultdict(int)
    for state in StateDict.itervalues():
        for interval, target_index in state.transition_map:
            frequency_db[target_index] += 1
    return frequency_db

