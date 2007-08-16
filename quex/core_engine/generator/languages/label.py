
def __nice(SM_ID): 
    return repr(SM_ID).replace("L", "")
    

def get(StateMachineName, StateIdx):
    if StateIdx == None: 
        raise "StateIdx == None; call function 'get_terminal' instead."

    return "QUEX_LABEL_%s_ENTRY_%s" % (StateMachineName, __nice(StateIdx))


def get_input(StateMachineName, StateIdx):

    return "QUEX_LABEL_%s_STATE_%s_GET_INPUT" % (StateMachineName, __nice(StateIdx))


def get_terminal(StateMachineName, TerminalStateIdx=None):

    if TerminalStateIdx == None:
        return "QUEX_LABEL_%s_TERMINAL" % StateMachineName
    else:       
        return "QUEX_LABEL_%s_TERMINAL_%s" % (StateMachineName, __nice(TerminalStateIdx))

def get_drop_out(StateMachineName, StateIdx):

    return "QUEX_LABEL_%s_%s_DROP_OUT" % (StateMachineName, __nice(StateIdx))
