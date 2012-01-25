import quex.engine.generator.state.core as state_coder
import quex.engine.generator.template_coder   as template_coder
import quex.engine.generator.paths_coder      as paths_coder
from   quex.blackboard                        import setup as Setup, E_Compression

from   collections import defaultdict
from   itertools   import imap

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

    # (*) Compression Algorithms:
    #     txt       -- is directly filled with code of compressed states.
    #     done_list -- contains list of state indices that have been combined.
    mega_state_list = []
    for ctype in Setup.compression_type_list:
        # -- Path-Compression
        if ctype in (E_Compression.PATH, E_Compression.PATH_UNIFORM):
            done_state_index_list, \
            template_state_list    = paths_coder.do(txt, TheAnalyzer, 
                                                    ctype, remainder, mega_state_list)
            remainder.difference_update(done_list)
            mega_state_list.extend(template_state_list)
    
        # -- Template-Compression
        elif ctype in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM):
            done_state_index_list, \
            pathwalker_state_list  = template_coder.do(txt, TheAnalyzer, Setup.compression_template_min_gain, 
                                                       ctype, remainder, mega_state_list)
            remainder.difference_update(done_list)
            mega_state_list.extend(template_state_list)
    
    # (*) All other (normal) states (sorted by their frequency of appearance
    frequency_db = get_frequency_db(TheAnalyzer.state_db, remainder)
    for state in sorted(imap(lambda i: TheAnalyzer.state_db[i], remainder), 
                        key=lambda s: frequency_db[s.index], reverse=True):
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

