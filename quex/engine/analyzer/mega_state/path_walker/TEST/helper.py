import quex.engine.analyzer.mega_state.path_walker.core  as     paths 
import quex.engine.analyzer.engine_supply_factory        as     engine
from   quex.engine.analyzer.core                         import Analyzer
from   quex.blackboard                                   import E_Compression

def find_core(sm):
    print sm.get_graphviz_string(NormalizeF=False)
    print
    analyzer = Analyzer(sm, engine.FORWARD)
    for state in analyzer.state_db.itervalues():
        state.entry.action_db.categorize(state.index)
    for state in analyzer.state_db.itervalues():
        state.transition_map = state.transition_map.relate_to_door_ids(analyzer, state.index)

    return paths.collect(analyzer, 
                         CompressionType=E_Compression.PATH, 
                         AvailableStateIndexList=analyzer.state_db.keys())

