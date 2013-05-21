# (C) 2012 Frank-Rene Schaefer
import quex.engine.analyzer.mega_state.template.core    as     template_analyzer
import quex.engine.analyzer.mega_state.path_walker.core as     path_analyzer
from   quex.engine.analyzer.mega_state.core             import AbsorbedState
from   quex.blackboard                                  import setup as Setup, \
                                                               E_Compression

def do(TheAnalyzer):
    """MegaState Analysis _____________________________________________________

    Normal states are potentially absorbed by MegaState-s which represent more
    than one single state at once.

    The setting 'Setup.compression_type_list' defines what type of algorithms
    have to be executed in to construct MegaStates (if any at all). Consider
    'core.py' in this directory for further reading.
    ___________________________________________________________________________
    """
    TheAnalyzer.mega_state_list = []

    # The 'remainder' keeps track of states which have not yet been
    # absorbed into a MegaState.
    remainder = set(TheAnalyzer.state_db.iterkeys())
    remainder.remove(TheAnalyzer.init_state_index)

    for ctype in Setup.compression_type_list:
        # -- MegaState-s by Path-Compression
        if ctype in (E_Compression.PATH, E_Compression.PATH_UNIFORM):
            mega_state_list = path_analyzer.do(TheAnalyzer, ctype, remainder)
    
        # -- MegaState-s by Template-Compression
        elif ctype in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM):
            mega_state_list = template_analyzer.do(TheAnalyzer, Setup.compression_template_min_gain, 
                                                   ctype, remainder)
        else:
            assert False

        # -- Post-process the absorption of AnalyzerState-s into MegaState-s
        for mega_state in mega_state_list:
            # Replace the absorbed AnalyzerState by its dummy.
            TheAnalyzer.state_db.update(
                 (state_index, AbsorbedState(TheAnalyzer.state_db[state_index], mega_state))
                 for state_index in mega_state.implemented_state_index_list()
            )

            # Track the remaining not-yet-absorbed states
            remainder.subtract(mega_state.implemented_state_index_list())

        TheAnalyzer.mega_state_list.extend(mega_state_list)

    # Let the analyzer know about the MegaState-s and what states they left
    # unabsorbed. 
    TheAnalyzer.non_mega_state_index_set = remainder
    TheAnalyzer.non_mega_state_index_set.add(TheAnalyzer.init_state_index)

    # Only now: We enter the MegaState-s into the 'state_db'. If it was done before,
    # the MegaStates might try to absorb each other.
    TheAnalyzer.state_db.update(
       (mega_state.index, mega_state) for mega_state in TheAnalyzer.mega_state_list
    )

    map_door_ids = {}
    for mega_state in TheAnalyzer.mega_state_list:
        map_door_ids.update(mega_state.entry.door_tree_configure())

    for state in TheAnalyzer.state_db.itervalues():
        state.transition_map.replace_door_ids(map_door_ids)

    for mega_state in TheAnalyzer.mega_state_list:
        mega_state.finalize_transition_map(TheAnalyzer.state_db)


