def do(InpStr, state_machine):
    """Enters the given string letter by letter into the given state machine 
       and shows the traces and results.
    """
    state_idx = state_machine.init_state_index
    msg = "[START] at " + repr(state_idx)
    success_f = False
    for letter in InpStr:
        state_idx, raise_success_f = state_machine.get_result(state_idx, ord(letter))
        if raise_success_f: success_f = True
        if success_f: msg += "=='%s'==>(**%s**)" % (letter, repr(state_idx).replace("L", ""))
        else:         msg += "=='%s'==>(%s)" % (letter, repr(state_idx).replace("L", ""))
    print msg
