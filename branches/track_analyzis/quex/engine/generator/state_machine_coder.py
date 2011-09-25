import quex.engine.generator.state_coder.core as     state_coder
from   quex.blackboard                        import setup as Setup
import quex.engine.generator.template_coder   as template_coder
import quex.engine.generator.paths_coder      as paths_coder

from   collections import defaultdict
from   itertools   import ifilter

def do(TheAnalyzer):
    """Generate source code for a given state machine 'SM'.
    """
    assert id(Setup.language_db.analyzer) == id(TheAnalyzer)

    txt = []

    # Track what states are treated with different methods (see below)
    remainder  = set(TheAnalyzer.state_db.keys())

    # (*) Init State
    state_coder.do(txt, TheAnalyzer.state_db[TheAnalyzer.init_state_index], TheAnalyzer)
    remainder.discard(TheAnalyzer.init_state_index)

    # (*) [Optional] Path-Compressed States
    if Setup.compression_path_f or Setup.compression_path_uniform_f:
        done_list = paths_coder.do(txt, TheAnalyzer, Setup.compression_path_uniform_f)
        remainder.difference_update(done_list)
    
    # (*) [Optional] Template-Compressed States
    if Setup.compression_template_f:
        done_list = template_coder.do(txt, TheAnalyzer, Setup.compression_template_coef)
        remainder.difference_update(done_list)
    
    # (*) All other (normal) states (sorted by their frequency of appearance
    frequency_db = get_frequency_db(TheAnalyzer.state_db, remainder)
    for state in sorted(ifilter(lambda x: x.index in remainder, TheAnalyzer.state_db.itervalues()), 
                        key=lambda x: frequency_db[x.index], reverse=True):
        state_coder.do(txt, state, TheAnalyzer) 

    LanguageDB = Setup.language_db
    LanguageDB.REPLACE_INDENT(txt)

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

