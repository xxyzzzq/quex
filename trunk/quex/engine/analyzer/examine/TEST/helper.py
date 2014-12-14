from quex.engine.operations.se_operations import SeAccept, SeStoreInputPosition
from quex.blackboard                      import E_PreContextIDs

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
