# (C) 2012 Frank-Rene Schaefer
import quex.engine.analyzer.mega_state.template.core    as     template_analyzer
import quex.engine.analyzer.mega_state.path_walker.core as     path_analyzer
from   quex.engine.analyzer.mega_state.core             import AbsorbedState, MegaState
from   quex.engine.analyzer.mega_state.target           import MegaState_Target
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
            remainder.difference_update(mega_state.implemented_state_index_list())

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

    _update_MegaState_door_ids(TheAnalyzer)

def _update_MegaState_door_ids(TheAnalyzer):
    """DoorID-s to to this point in time relate to origanl AnalyzerState-s.
       Since the CommandList-s are now implemented in MegaState-s and since
       they might profit from being the same, they are categorized again
       and new DoorID-s are assigned according to the MegaState which 
       implements them.

       The transition maps are adapted accordingly.
    """
    # Determine new DoorID-s in MegaState-s
    map_old_to_new_door_id = {}
    for mega_state in TheAnalyzer.mega_state_list:
        replacement_db = mega_state.entry.action_db.categorize(mega_state.index)
        if replacement_db is not None:
            map_old_to_new_door_id.update(replacement_db)

    # Replace the old by new DoorID-s
    for state in TheAnalyzer.state_db.itervalues():
        if isinstance(state, AbsorbedState): 
            continue
        elif isinstance(state, MegaState):
            state.transition_map.replace_DoorIDs_in_MegaStateTargets(map_old_to_new_door_id)
            MegaState_Target.rejoin_uniform_schemes(state.transition_map)
            MegaState_Target.assign_scheme_ids(state.transition_map)
        else:
            state.transition_map.replace_DoorIDs(map_old_to_new_door_id)

        # Before: Adjacent intervals had a different targets (DoorID-s).
        # After:  Adjacent intervals CANNOT have the same target, either.
        # 
        # Proof: 
        # (0) Adjacent intervals have different targets.
        # (1) Two targets 'x' and 'y' in an AnalyzerState relate to two
        #     different target states.
        # (2) A MegaState which implements a state 'x' or 'y' does so by
        #     setting a 'key' at the entry which represents the state. This
        #     key is unique for each state. 
        # (3) The 'set-key' command for 'x' and 'y' differs. Otherwise,
        #     the key would not identify a state.
        # (4) It follows from (3) that the CommandLists() at the entry
        #     of the MegaState differ. It depends whether the MegaState
        #     represents 'x' or 'y'.
        # (5) Since the CommandList-s differ, EntryActionDB.categorize()
        #     will assign different DoorID-s. 
        #  => For each two different targets 'x' and 'y' in a transition
        #     map, it holds that their replacements also differ.
        #  => from (0) it holds that adjacent intervals have different
        #     targets after the replacement operation in the transition map.
        state.transition_map.assert_continuity()

