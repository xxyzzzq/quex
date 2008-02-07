import sys

import quex.lexer_mode as lexer_mode

def do(Modes):
    """If consistency check fails due to a fatal error, then this functions
    exits back to the system with error code -1.  Otherwise, in 'not so
    perfect' cases there might be only a warning being printed to standard
    output.
    """
    if len(Modes) == 0:
        print "error: no single mode defined - bailing out"
        sys.exit(-1)

    # is there a mode that is applicable?
    for mode in Modes.values():
        if mode.options["inheritable:"] != "only": break
    else:
        print "error: There is no mode that can be applied---all existing modes are 'inheritable only'."
        print "error: modes are = ", map(lambda m: m.name, Modes.values())
        sys.exit(-1)

    # is the initial mode defined
    if lexer_mode.initial_mode.line_n == -1:
        # find first mode that can actually be applied
        for mode in Modes.values():
            if mode.options["inheritable:"] != "only":
                selected_mode = mode.name
                break
            
        lexer_mode.initial_mode.code     = selected_mode
        lexer_mode.initial_mode.line_n   = 0
        lexer_mode.initial_mode.filename = "automatical-selection-by-quex"
        print "warning: no initial mode defined via 'start'"
        print "warning: using mode '%s' as initial mode" % selected_mode
                
    for mode in Modes.values():
        mode.consistency_check()
