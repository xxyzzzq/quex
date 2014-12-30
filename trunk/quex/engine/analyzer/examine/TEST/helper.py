from quex.engine.operations.se_operations    import SeAccept, SeStoreInputPosition
from quex.engine.analyzer.examine.acceptance import RecipeAcceptance
from quex.blackboard                         import E_PreContextIDs, E_R, E_IncidenceIDs


class DerivedRecipe(RecipeAcceptance):
    rr_by_state_db = {}

    @staticmethod
    def get_RR_superset(sm, StateIndex, PredecessorDb):
        result = set(
            (E_R.PositionRegister, register_id)
            for register_id in DerivedRecipe.position_register_by_state_db[StateIndex]
        )
        result.add((E_R.PositionRegister, E_IncidenceIDs.MATCH_FAILURE))
        result.add(E_R.AcceptanceRegister)
        return result

def get_SeAccept(AcceptanceId, PreContextId, RestorePositionF=False):
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
