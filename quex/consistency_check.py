import sys

from   quex.frs_py.file_in import error_msg
import quex.lexer_mode     as     lexer_mode
from   quex.core_engine.generator.action_info import CodeFragment


def do(ModeDB):
    """Consistency check of mode database

       -- Are there applicable modes?
       -- Start mode:
          -- specified (more than one applicable mode req. explicit specification)?
          -- is defined as mode?
          -- start mode is not inheritable only?
       -- Entry/Exit transitions are allows?
    """
    if len(ModeDB) == 0:
        error_msg("No single mode defined - bailing out", Prefix="consistency check")

    mode_name_list            = map(lambda mode:        mode.name, ModeDB.values())
    mode_name_list.sort()
    applicable_mode_name_list = map(lambda mode:        mode.name, 
                                    filter(lambda mode: mode.options["inheritable"] != "only",
                                           ModeDB.values()))
    applicable_mode_name_list.sort()

    # (*) Is there a mode that is applicable?
    #     That is: is there a more that is not only inheritable?
    if len(applicable_mode_name_list) == 0:
        error_msg("There is no mode that can be applied---all existing modes are 'inheritable only'.\n" + \
                  "modes are = " + repr(mode_name_list)[1:-1],
                  Prefix="consistency check")

    # (*) Start mode specified?
    #     More then one mode definition requires an explicit definition 'start = mode'.
    start_mode = lexer_mode.initial_mode.get_pure_code()
    if start_mode == "":
        # Choose an applicable mode as start mode
        start_mode              = applicable_mode_name_list[0]
        lexer_mode.initial_mode = CodeFragment(start_mode)
        if len(applicable_mode_name_list) > 1:
            error_msg("No initial mode defined via 'start' while more than one applicable mode exists.\n" + \
                      "Use for example 'start = %s;' in the quex source file to define an initial mode." \
                      % start_mode)

        # This Branch: start mode is applicable and present

    else: 
        FileName = lexer_mode.initial_mode.filename
        LineN    = lexer_mode.initial_mode.lineN
        # Start mode present and applicable?
        verify_word_in_list(start_mode, mode_name_list,
                            "Start mode '%s' is not defined." % start_mode,
                            FileName, LineN)
        verify_word_in_list(start_mode, applicable_mode_name_list,
                            "Start mode '%s' is inheritable only and cannot be instantiated." % start_mode,
                            FileName, LineN)

    # (*) Entry/Exit Transitions
    for this_mode in ModeDB.values():
        for mode_name in this_mode.options["exit"]:

            verify_word_in_list(mode_name, mode_name_list,
                                "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                                (this_mode.name, mode_name),
                                FileName, LineN)


            that_mode = mode_description_db[mode_name]

            # Other mode allows all entries => don't worry.
            if len(that_mode.options["entry"]) == 0: continue

            # Other mode restricts the entries from other modes
            # => check if this mode or one of the base modes can enter
            for base_mode in this_mode.get_base_mode_sequence():
                if base_mode in that_mode.options["entry"]: break
            else:
                error_msg("Mode '%s'\nhas an exit to mode '%s'," % (this_mode.name, mode_name),
                          this_mode.filename, this_mode.line_n, DontExitF=True, WarningF=False)
                error_msg("but mode '%s'\nhas no entry for mode '%s'.\n" % (mode_name, this_mode.name) + \
                          "or any of its base modes.",
                          that_mode.filename, that_mode.line_n)

        for mode_name in this_mode.options["entry"]:
            # Does that mode exist?
            verify_word_in_list(mode_name, mode_name_list,
                                "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                                (this_mode.name, mode_name),
                                FileName, LineN)

            that_mode = mode_description_db[mode_name]
            # Other mode allows all exits => don't worry.
            if len(that_mode.options["exit"]) == 0: continue

            # Other mode restricts the exits to other modes
            # => check if this mode or one of the base modes can be reached
            for base_mode in this_mode.get_base_mode_sequence():
                if base_mode in that_mode.options["exit"]: break
            else:
                error_msg("Mode '%s'\nhas an entry for mode '%s'" % (this_mode.name, mode_name),
                          this_mode.filename, this_mode.line_n, DontExitF=True, WarningF=False)
                error_msg("but mode '%s'\nhas no exit to mode '%s'\n" % (mode_name, this_mode.name) + \
                          "or any of its base modes.",
                          that_mode.filename, that_mode.line_n)
                
    # -- mode specific checks
    for mode in ModeDB.values():
        mode.consistency_check()

