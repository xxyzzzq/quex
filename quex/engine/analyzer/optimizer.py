from   quex.engine.state_machine.state_core_info import E_EngineTypes

from   itertools import imap

def do(analyzer):
    if analyzer.engine_type != E_EngineTypes.FORWARD:
        return analyzer

    # If a state has no successor state, or only transitions to itself,
    # => No accepter check is necessary, done in drop-out
    for state_index, state in analyzer.state_db.iteritems():
        tm = state.transition_map
        if   len(tm) == 0: 
            state.entry.accepter.clear()
        elif (len(tm) == 1 and tm[0][1] == state_index):
            state.entry.accepter.clear()

    for entry in imap(lambda x: x.entry, analyzer.state_db.itervalues()):
        entry.try_unify_positioner_db()

    return analyzer


