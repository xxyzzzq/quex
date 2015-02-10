from quex.engine.operations.se_operations    import SeAccept, SeStoreInputPosition
from quex.engine.analyzer.examine.acceptance import RecipeAcceptance
from quex.blackboard                         import E_PreContextIDs, E_R, E_IncidenceIDs


class DerivedRecipe(RecipeAcceptance):
    position_register_by_state_db = {}

    @staticmethod
    def get_RR_superset(sm, StateIndex, PredecessorDb):
        result = set(
            (E_R.PositionRegister, register_id)
            for register_id in DerivedRecipe.position_register_by_state_db[StateIndex]
        )
        result.add((E_R.PositionRegister, E_IncidenceIDs.MATCH_FAILURE))
        result.add(E_R.AcceptanceRegister)
        return result

def get_SeAccept(AcceptanceId, PreContextId=E_PreContextIDs.NONE, RestorePositionF=False):
    cmd = SeAccept()
    cmd.set_acceptance_id(AcceptanceId)
    cmd.set_pre_context_id(PreContextId)
    if RestorePositionF:
        cmd.set_restore_position_register_f()
    return cmd

def add_SeAccept(sm, StateIndex, AcceptanceId, PreContextId=E_PreContextIDs.NONE, RestorePositionF=False):
    sm.states[StateIndex].single_entry.add(get_SeAccept(AcceptanceId, PreContextId, RestorePositionF))
    accept_str  = "%s" % AcceptanceId
    pre_str     = "%s/" % PreContextId if PreContextId != E_PreContextIDs.NONE else ""
    restore_str = "R" if RestorePositionF else ""
    print "(%i) Accept %s%s%s" % (StateIndex, pre_str, accept_str, restore_str)

def add_SeStoreInputPosition(sm, StateIndex, RegisterId):
    sm.states[StateIndex].single_entry.add(SeStoreInputPosition(RegisterId))
    print "(%i) Store InputP %s" % (StateIndex, RegisterId)

def print_recipe(si, R):
    if R is None: 
        print "  %02i <void>" % si
    else:
        print "  %02i %s" % (si, str(R).replace("\n", "\n     "))

def print_mouth(si, Mouth):
    print_recipe(si, Mouth.recipe)
    print_snapshot_map(Mouth.recipe.snapshot_map)
    print_entry_recipe_db(Mouth.entry_recipe_db)

def print_snapshot_map(SnapshotMap):
    print "  snapshot_map: [%s]" % "".join("%s@%s" % (x,y) for x,y in SnapshotMap.iteritems())

def print_entry_recipe_db(EntryRecipeDb):
    for predecessor_si, entry_recipe in EntryRecipeDb.iteritems():
        print "  from %i:" % predecessor_si
        print entry_recipe


