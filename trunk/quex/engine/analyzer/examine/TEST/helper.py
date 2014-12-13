from quex.engine.operations.se_operations                       import SeAccept

def get_SeAccept(AcceptanceId, PreContextId, RestorePositionF=False):
    cmd = SeAccept()
    cmd.set_acceptance_id(AcceptanceId)
    cmd.set_pre_context_id(PreContextId)
    if RestorePositionF:
        cmd.set_restore_position_register_f()
    return cmd
