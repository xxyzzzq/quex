import quex.engine.state_machine.algorithm.beautifier         as beautifier

def do(the_state_machine, BIPD_to_be_inverted):
    # Only now, after the transformation we can safely get the inverse 
    # state machine which is able to detect backwards.
    sm = beautifier.do(BIPD_to_be_inverted.get_inverse())
    sm.mark_state_origins() # Origins tell about pattern that is served.
    # We must communicate the transformed state machine back to the pattern
    return sm
