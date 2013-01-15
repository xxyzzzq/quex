
def do(SM):
    """Cut all 'Eat-All' states from state machine."""
    result = SM.clone()
    for state_index, state in result.states.items():
        tm = state.transitions().get_map()
        if len(tm) != 1: continue
        target_index, trigger_set = tm.iteritems().next()
        if target_index != state_index: continue
        if not trigger_set.is_all(): continue
        # 'Eat-All' will become a hopeless state and 'clean_up' will delete it.
        state.set_acceptance(False)

    result.clean_up()

    return result
