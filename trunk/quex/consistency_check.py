import sys

from   quex.frs_py.file_in import error_msg
import quex.lexer_mode     as     lexer_mode

def do(Modes):
    """If consistency check fails due to a fatal error, then this functions
    exits back to the system with error code -1.  Otherwise, in 'not so
    perfect' cases there might be only a warning being printed to standard
    output.
    """
    if len(Modes) == 0:
        error_msg("No single mode defined - bailing out", Prefix="consistency check")

    # -- is there a mode that is applicable?
    for mode in Modes.values():
        if mode.options["inheritable:"] != "only": break
    else:
        error_msg("There is no mode that can be applied---all existing modes are 'inheritable only'.\n" + \
                "modes are = " + repr(map(lambda m: m.name, Modes.values()))[1:-1],
                  Prefix="consistency check")

    # -- is the initial mode defined
    if lexer_mode.initial_mode.line_n == -1:
        # find first mode that can actually be applied
        for mode in Modes.values():
            if mode.options["inheritable:"] != "only":
                selected_mode = mode.name
                break
            
        lexer_mode.initial_mode.code     = selected_mode
        lexer_mode.initial_mode.line_n   = 0
        lexer_mode.initial_mode.filename = "automatical-selection-by-quex"
        error_msg("no initial mode defined via 'start'\n" + \
                  "using mode '%s' as initial mode" % selected_mode, DontExitF=True,
                  Prefix="warning")


    # -- is the start mode applicable?
    if Modes.has_key(lexer_mode.initial_mode.code) == False:
        error_msg("Start mode '%s' has not been defined anywhere." % lexer_mode.initial_mode.code,
                  lexer_mode.initial_mode.filename, lexer_mode.initial_mode.line_n)

    if Modes[lexer_mode.initial_mode.code].options["inheritable:"] == "only":
        error_msg("Start mode '%s' is inheritable only and cannot be instantiated." % lexer_mode.initial_mode.code,
                  lexer_mode.initial_mode.filename, lexer_mode.initial_mode.line_n)

                
    # -- mode specific checks
    for mode in Modes.values():
        mode.consistency_check()
