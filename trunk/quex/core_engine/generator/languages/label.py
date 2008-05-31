
def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")
    

def get(StateMachineName, StateIdx, DeadEndStateDB, BackwardLexingF):
    # For transitions jumps may need to be redirected to terminal states.
    # for this the 'DeadEndStateDB' and the BackwardLexingF must be known.
    # For any other case, the dead end state db and the backward lexing
    # flag are irrelevant.
    assert StateIdx != None, "StateIdx == None; call function 'get_terminal' instead."
    assert BackwardLexingF!=None or DeadEndStateDB == {}
    assert type(DeadEndStateDB) == dict
    assert type(BackwardLexingF) == bool or BackwardLexingF == None

    if DeadEndStateDB.has_key(StateIdx):
        if DeadEndStateDB[StateIdx] == -1:   
            return get_terminal(None, BackwardLexingF)
        elif DeadEndStateDB[StateIdx] != None: 
            return get_terminal(DeadEndStateDB[StateIdx], BackwardLexingF)
        # if the dead end was of type 'None' this means that it depends on
        # pre-conditions and the state is implemented as router that routes
        # to a terminal dependent on the run-time setting of pre-conditions.

    return "STATE_%s" % __nice(StateIdx)


def get_input(StateIdx):

    return "STATE_%s_INPUT" % __nice(StateIdx)


def get_terminal(TerminalStateIdx=None, BackwardLexingF=False):

    if TerminalStateIdx == None:
        if BackwardLexingF: return "TERMINAL_GENERAL_PRE_CONTEXT"
        else:               return "TERMINAL_GENERAL"
    else:       
        return "TERMINAL_%s" % __nice(TerminalStateIdx)

def get_drop_out(StateIdx):

    return "STATE_%s_DROP_OUT" % __nice(StateIdx)
