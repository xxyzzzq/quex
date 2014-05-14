import quex.engine.generator.state.core      as     state_coder
import quex.engine.generator.state.entry     as     entry
import quex.engine.generator.mega_state.core as     mega_state_coder
from   quex.blackboard                       import setup as Setup, Lng

from   collections import defaultdict
from   itertools   import imap

from   copy        import copy

def do(TheAnalyzer):
    """Generate source code for a given state machine 'SM'.
    """
    Lng.register_analyzer(TheAnalyzer)
    
    assert id(Lng.analyzer) == id(TheAnalyzer)

    # (*) Init State must be first!
    txt = []
    state_coder.do(txt, TheAnalyzer.state_db[TheAnalyzer.init_state_index], TheAnalyzer)

    # (*) The drop-out catcher, since it is referenced the most.
    result, dummy = entry.do(TheAnalyzer.drop_out, TheAnalyzer)
    txt.extend(result)
    txt.append(Lng.UNREACHABLE)

    # (*) Code the Mega States (implementing multiple states in one)
    for state in TheAnalyzer.mega_state_list:
        mega_state_coder.do(txt, state, TheAnalyzer)

    # (*) All other (normal) states (sorted by their frequency of appearance)
    frequency_db = get_frequency_db(TheAnalyzer.state_db, 
                                    TheAnalyzer.non_mega_state_index_set)
    remainder    = copy(TheAnalyzer.non_mega_state_index_set)
    remainder.remove(TheAnalyzer.init_state_index)
    for state in sorted(imap(lambda i: TheAnalyzer.state_db[i], remainder), 
                        key=lambda s: frequency_db[s.index], reverse=True):
        state_coder.do(txt, state, TheAnalyzer) 

    Lng.unregister_analyzer()
    return txt

def get_frequency_db(StateDB, RemainderStateIndexList):
    """Sort the list in a away, so that states that are used more
       often appear earlier. This happens in the hope of more 
       cache locality. 
    """
    # Count number of transitions to a state: frequency_db
    frequency_db = defaultdict(int)
    for state in (StateDB[i] for i in RemainderStateIndexList):
        assert state.transition_map is not None
        for interval, target_index in state.transition_map:
            frequency_db[target_index] += 1
    return frequency_db

