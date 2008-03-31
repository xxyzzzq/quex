
def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")
    

def get(StateMachineName, StateIdx):
    assert StateIdx != None, "StateIdx == None; call function 'get_terminal' instead."

    return "STATE_%s" % __nice(StateIdx)


def get_input(StateMachineName, StateIdx):

    return "STATE_%s_INPUT" % __nice(StateIdx)


def get_terminal(StateMachineName, TerminalStateIdx=None):

    if TerminalStateIdx == None:
        ## return "QUEX_LABEL_%s_TERMINAL" % StateMachineName
        return "GENERAL_%s_TERMINAL" % StateMachineName
        ## return "GENERAL_TERMINAL"
    else:       
        ## return "QUEX_LABEL_%s_TERMINAL_%s" % (StateMachineName, __nice(TerminalStateIdx))
        return "TERMINAL_%s" % __nice(TerminalStateIdx)

def get_drop_out(StateMachineName, StateIdx):

    return "STATE_%s_DROP_OUT" % __nice(StateIdx)
