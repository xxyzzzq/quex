
def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")
    

def get(StateMachineName, StateIdx, DeadEndStateDB, BackwardLexingF):
    # For transitions jumps may need to be redirected to terminal states.
    # for this the 'DeadEndStateDB' and the BackwardLexingF must be known.
    # For any other case, the dead end state db and the backward lexing
    # flag are irrelevant.
    assert StateIdx != None, "StateIdx == None; call function 'get_terminal' instead."

    return "STATE_%s" % __nice(StateIdx)

def get_input(StateIdx):

    return "STATE_%s_INPUT" % __nice(StateIdx)

def get_terminal(TerminalStateIdx=None, BackwardLexingF=False, WithoutSeekAdrF=False):

    if TerminalStateIdx == None:
        if BackwardLexingF: return "TERMINAL_GENERAL_PRE_CONTEXT"
        else:               return "TERMINAL_GENERAL"
    else:       
        if not WithoutSeekAdrF: return "TERMINAL_%s"              % __nice(TerminalStateIdx)
        else:                   return "TERMINAL_%s_WITHOUT_SEEK" % __nice(TerminalStateIdx)

def get_drop_out(StateIdx):

    return "STATE_%s_DROP_OUT" % __nice(StateIdx)
