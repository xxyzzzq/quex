import quex.engine.generator.state.core      as state_coder
import quex.engine.analyzer.template.core    as template_analyzer
from   quex.engine.analyzer.template.state   import TemplateState
import quex.engine.analyzer.path.core        as path_analyzer
import quex.engine.generator.template_coder  as template_coder
import quex.engine.generator.paths_coder     as paths_coder
from   quex.blackboard                       import setup as Setup, E_Compression

from   collections import defaultdict
from   itertools   import imap

def do(TheAnalyzer):
    """Generate source code for a given state machine 'SM'.
    """

    assert id(Setup.language_db.analyzer) == id(TheAnalyzer)

    # Track what states are treated with different methods (see below)
    remainder  = set(TheAnalyzer.state_db.keys())
    # The init state shall never be part of a mega state
    remainder.discard(TheAnalyzer.init_state_index)

    # (*) Analyzer to generate Mega States (multiple states compressed into one)
    mega_state_list, remainder = mega_state_analyzer(TheAnalyzer, remainder)

    # (*) Init State must be first!
    txt = []
    state_coder.do(txt, TheAnalyzer.state_db[TheAnalyzer.init_state_index], TheAnalyzer)

    # (*) Code the Mega States (implementing multiple states in one)
    mega_state_coder(txt, mega_state_list, TheAnalyzer)

    # (*) All other (normal) states (sorted by their frequency of appearance)
    frequency_db = get_frequency_db(TheAnalyzer.state_db, remainder)
    for state in sorted(imap(lambda i: TheAnalyzer.state_db[i], remainder), 
                        key=lambda s: frequency_db[s.index], reverse=True):
        state_coder.do(txt, state, TheAnalyzer) 

    LanguageDB = Setup.language_db
    LanguageDB.REPLACE_INDENT(txt)

    return txt

def mega_state_analyzer(TheAnalyzer, remainder):
    mega_state_list = []
    for ctype in Setup.compression_type_list:
        # -- Path-Compression
        if ctype in (E_Compression.PATH, E_Compression.PATH_UNIFORM):
            done_state_index_list, \
            pathwalker_state_list  = path_analyzer.do(TheAnalyzer, ctype, 
                                                      remainder, mega_state_list)
            remainder.difference_update(done_list)
            mega_state_list.extend(pathwalker_state_list)
    
        # -- Template-Compression
        elif ctype in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM):
            done_state_index_list, \
            template_state_list    = template_analyzer.do(TheAnalyzer, Setup.compression_template_min_gain, ctype, 
                                                          remainder, mega_state_list)
            remainder.difference_update(done_state_index_list)
            mega_state_list.extend(template_state_list)

    return mega_state_list, remainder

def mega_state_coder(txt, MegaStateList, TheAnalyzer):
    for state in MegaStateList:
        if isinstance(state, TemplateState):
            template_coder.do(txt, state, TheAnalyzer)
        elif isinstance(state, PathWalkerState):
            path_coder.do(state)

    return 

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

