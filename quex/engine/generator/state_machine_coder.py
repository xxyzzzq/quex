import quex.engine.generator.state.core                 as     state_coder
import quex.engine.generator.mega_state.core            as     mega_state_coder
from   quex.blackboard                                  import setup as Setup

from   collections import defaultdict
from   itertools   import imap

def do(TheAnalyzer, BeforeReloadAction=None):
    """Generate source code for a given state machine 'SM'.
    """
    LanguageDB = Setup.language_db
    assert id(LanguageDB.analyzer) == id(TheAnalyzer)

    # (*) Init State must be first!
    txt = []
    state_coder.do(txt, TheAnalyzer.state_db[TheAnalyzer.init_state_index], TheAnalyzer, BeforeReloadAction)

    # (*) Code the Mega States (implementing multiple states in one)
    for state in TheAnalyzer.mega_state_list:
        mega_state_coder.do(txt, state, TheAnalyzer, BeforeReloadAction)

    # (*) All other (normal) states (sorted by their frequency of appearance)
    frequency_db = get_frequency_db(TheAnalyzer.state_db, TheAnalyzer.non_mega_state_index_set)
    for state in sorted(imap(lambda i: TheAnalyzer.state_db[i], TheAnalyzer.non_mega_state_index_set), 
                        key=lambda s: frequency_db[s.index], reverse=True):
        state_coder.do(txt, state, TheAnalyzer, BeforeReloadAction) 

    return txt

def get_frequency_db(StateDB, RemainderStateIndexList):
    """Sort the list in a away, so that states that are used more
       often appear earlier. This happens in the hope of more 
       cache locality. 
    """
    # Count number of transitions to a state: frequency_db
    frequency_db = defaultdict(int)
    for state in (StateDB[i] for i in RemainderStateIndexList):
        for interval, target_index in state.transition_map:
            frequency_db[target_index] += 1
    return frequency_db

