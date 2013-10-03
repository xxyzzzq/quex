import quex.engine.analyzer.mega_state.path_walker.core  as     paths 
import quex.engine.analyzer.mega_state.path_walker.find  as     find
import quex.engine.analyzer.engine_supply_factory        as     engine
from   quex.engine.analyzer.core                         import Analyzer
from   quex.blackboard                                   import E_Compression

def find_core(sm, SelectF=False):
    print sm.get_graphviz_string(NormalizeF=False)
    print
    analyzer = Analyzer(sm, engine.FORWARD)
    for state in analyzer.state_db.itervalues():
        state.entry.action_db.categorize(state.index)
    for state in analyzer.state_db.itervalues():
        if state.transition_map is None: continue
        state.transition_map = state.transition_map.relate_to_DoorIDs(analyzer, state.index)

    AvailableStateIndexSet = set(analyzer.state_db.keys())
    CompressionType        = E_Compression.PATH
    result = find.do(analyzer, 
                     CompressionType=CompressionType, 
                     AvailableStateIndexSet=AvailableStateIndexSet)

    if SelectF:
        result = paths.select(result)
        paths.path_list_assert_consistency(result, analyzer, AvailableStateIndexSet, CompressionType)

    return result

