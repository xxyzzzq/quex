from   quex.engine.analyzer.mega_state.core             import AbsorbedState
import quex.engine.analyzer.mega_state.template.core    as     template_analyzer
import quex.engine.analyzer.mega_state.path_walker.core as     path_analyzer
from   quex.blackboard                                  import E_Compression
from   quex.blackboard                                  import setup as Setup

def do(TheAnalyzer):
    """Build the MegaState-s.
    
       Normal states are now absorbed by MegaState-s which represent
       more than one single state at once.
    """
    mega_state_db = {}
    # -- The 'remainder' keeps track of states which have not yet been
    #    absorbed into a MegaState.
    remainder = set(TheAnalyzer.state_db.keys())
    remainder.remove(TheAnalyzer.init_state_index)

    for ctype in Setup.compression_type_list:
        mega_state_list = mega_state_db.values()
        # -- MegaState-s by Path-Compression
        if ctype in (E_Compression.PATH, E_Compression.PATH_UNIFORM):
            absorbance_db = path_analyzer.do(TheAnalyzer, ctype, 
                                             remainder, mega_state_list)
    
        # -- MegaState-s by Template-Compression
        elif ctype in (E_Compression.TEMPLATE, E_Compression.TEMPLATE_UNIFORM):
            absorbance_db = template_analyzer.do(TheAnalyzer, 
                                                 Setup.compression_template_min_gain, ctype, 
                                                 remainder, mega_state_list)
        else:
            assert False

        # -- Post-process the absorption of AnalyzerState-s into MegaState-s
        for state_index, mega_state in absorbance_db.iteritems():
            # Replace the absorbed AnalyzerState by its dummy.
            TheAnalyzer.state_db[state_index] = \
                        AbsorbedState(TheAnalyzer.state_db[state_index], mega_state)

            # Track the remaining not-yet-absorbed states
            assert state_index in remainder
            remainder.remove(state_index)

            # Track MegaStates. A 'itervalues()' may contain the same MegaState
            # twice. Use a dictionary to keep them unique.
            if mega_state not in mega_state_db:
                mega_state_db[mega_state.index] = mega_state 

    # Let the analyzer know about the MegaState-s and what states they left
    # unabsorbed. 
    TheAnalyzer.non_mega_state_index_set = remainder
    TheAnalyzer.mega_state_list          = mega_state_db.values()
    # Only now: We enter the MegaState-s into the 'state_db'. If it was done before,
    # the MegaStates might try to absorb each other.
    TheAnalyzer.state_db.update(mega_state_db)


def __transition_adaption(TheAnalyzer, NewMegaStateList, OldMegaStateList):
    """Some AnalyzerState objects have been implemented in Mega States that 
       contain multiple states in once. Thus, the transitions to those AnalyzerState-s
       must be related to doors in the Mega State. This is what happens inside
       the present function.
    """
    # For the states that the new mega states implement, the doors need to 
    # be redirected from the original states to doors of the mega states.
    door_id_replacement_db = {}
    for mega_state in NewMegaStateList:
        door_id_replacement_db.update(mega_state.entry.door_id_replacement_db)

    # We must leave the databases in place, until the replacements are made
    for mega_state in NewMegaStateList:
        for state in (TheAnalyzer.state_db[i] for i in mega_state.implemented_state_index_list()):
            # Make sure, that the databases which are referenced for transition addresses
            # are updated, i.e. we use the ones of the template state.
            state.entry.set_door_db(mega_state.entry.door_db)
            state.entry.set_transition_db(mega_state.entry.transition_db)
            state.entry.set_door_tree_root(mega_state.entry.door_tree_root)
    return
