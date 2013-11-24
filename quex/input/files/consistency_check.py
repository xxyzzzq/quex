from   quex.engine.misc.file_in                    import error_msg, verify_word_in_list
from   quex.input.setup                            import NotificationDB
import quex.blackboard                             as     blackboard
from   quex.blackboard                             import setup as Setup, E_IncidenceIDs_Subset_Special
import quex.engine.state_machine.check.outrun      as     outrun_checker
import quex.engine.state_machine.check.superset    as     superset_check
import quex.engine.state_machine.check.same        as     same_check
from   itertools import islice


def do(ModeDB):
    """Consistency check of mode database

       -- Are there applicable modes?
       -- Start mode:
          -- specified (more than one applicable mode req. explicit specification)?
          -- is defined as mode?
          -- start mode is not inheritable only?
       -- Entry/Exit transitions are allows?
    """
    if Setup.token_class_only_f:
        if len(ModeDB) != 0:
            error_msg("Modes found in input files. However, only a token class is generated.", DontExitF=True)
        return

    if len(ModeDB) == 0:
        error_msg("No single mode defined - bailing out", Prefix="consistency check")

    mode_name_list             = sorted([mode.name for mode in ModeDB.itervalues()]) 
    # Applicable modes can only be determined after possible addition of "inheritable: only"
    implemented_mode_name_list = sorted([mode.name for mode in ModeDB.itervalues() if not mode.abstract_f()]) 

    if len(implemented_mode_name_list) == 0:
        error_msg("There is no mode that can be implemented---all existing modes are 'inheritable only'.\n" + \
                  "modes are = " + repr(ModeDB.keys())[1:-1],
                  Prefix="consistency check")

    for mode in ModeDB.values():
        mode.check_consistency()

    # (*) If a conversion or a codec engine is specified, then the 
    #     'on_codec_error' handler must be specified in every mode.
    if Setup.buffer_codec != "unicode" or Setup.converter_f:
        for mode in ModeDB.values():
            if E_IncidenceIDs.CODEC_ERROR not in mode.incidence_db:
                error_msg("Missing 'on_codec_error' handler in mode '%s' (or its base modes).\n" % mode.name + \
                          "This is dangerous while using a codec engine or a converter (iconv, icu, ...).\n" + \
                          "The feature is not yet supported, but the infrastructure is currently setup for it.",
                          mode.sr.file_name, mode.sr.line_n, DontExitF=True, WarningF=True, 
                          SuppressCode=NotificationDB.warning_codec_error_with_non_unicode)

    # (*) Start mode specified?
    __start_mode(implemented_mode_name_list, mode_name_list)

    # (*) Entry/Exit Transitions
    for mode in ModeDB.values():
        if mode.abstract_f(): continue
        __entry_exit_transitions(mode, mode_name_list)

    for mode in ModeDB.values():
        # (*) [Optional] Warnings on Outrun
        if Setup.warning_on_outrun_f:
             mode.check_low_priority_outruns_high_priority_pattern()

        # (*) Special Patterns shall not match on same lexemes
        if NotificationDB.error_on_special_pattern_same not in Setup.suppressed_notification_list:
            mode.check_match_same(NotificationDB.error_on_special_pattern_same)

        # (*) Special Patterns (skip, indentation, etc.) 
        #     shall not be outrun by another pattern.
        if NotificationDB.error_on_special_pattern_outrun not in Setup.suppressed_notification_list:
            mode.check_special_incidence_outrun(NotificationDB.error_on_special_pattern_outrun)

        # (*) Special Patterns shall not have common matches with patterns
        #     of higher precedence.
        if NotificationDB.error_on_special_pattern_subset not in Setup.suppressed_notification_list:
            mode.check_higher_priority_matches_subset(NotificationDB.error_on_special_pattern_subset)

        # (*) Check for dominated patterns
        if NotificationDB.error_on_dominated_pattern not in Setup.suppressed_notification_list:
            mode.check_dominated_pattern(NotificationDB.error_on_dominated_pattern)

def __error_message(This, That, ThisComment, ThatComment="", EndComment="", ExitF=True, SuppressCode=None):
    
    def get_name(PAP, AddSpaceF=True):
        print "#PAP:", PAP.__class__
        if PAP.comment in E_IncidenceIDs_Subset_Special: 
            result = repr(PAP.comment).replace("_", " ").lower()
        elif isinstance(PAP.comment, (str, unicode)):
            result = PAP.comment
        else:
            return ""

        if AddSpaceF and len(result) != 0: result += " "
        return result

    file_name, line_n = This.action().sr
    error_msg("The %spattern '%s' %s" % (get_name(This), This.pattern_string(), ThisComment), 
              file_name, line_n, 
              DontExitF=True, WarningF=not ExitF)

    FileName, LineN   = That.action().sr
    if len(ThatComment) != 0: Space = " "
    else:                     Space = ""

    msg = "%s%s%spattern '%s'." % (ThatComment, Space, get_name(That, AddSpaceF=True), That.pattern_string())
    if len(EndComment) == 0:
        error_msg(msg,        FileName, LineN, DontExitF=not ExitF, WarningF=not ExitF, SuppressCode=SuppressCode)
    else:
        error_msg(msg,        FileName, LineN, DontExitF=True,      WarningF=not ExitF)
        error_msg(EndComment, FileName, LineN, DontExitF=not ExitF, WarningF=not ExitF, SuppressCode=SuppressCode)

def __start_mode(implemented_mode_name_list, mode_name_list):
    """If more then one mode is defined, then that requires an explicit 
       definition 'start = mode'.
    """
    assert len(implemented_mode_name_list) != 0

    assert blackboard.initial_mode is not None

    start_mode = blackboard.initial_mode.get_pure_code()
    FileName   = blackboard.initial_mode.sr.file_name
    LineN      = blackboard.initial_mode.sr.line_n
    # Start mode present and applicable?
    verify_word_in_list(start_mode, mode_name_list,
                        "Start mode '%s' is not defined." % start_mode,
                        FileName, LineN)
    verify_word_in_list(start_mode, implemented_mode_name_list,
                        "Start mode '%s' is inheritable only and cannot be instantiated." % start_mode,
                        FileName, LineN)

def __entry_exit_transitions(mode, mode_name_list):
    FileName = mode.sr.file_name
    LineN    = mode.sr.line_n
    for mode_name in mode.exit_mode_name_list:
        verify_word_in_list(mode_name, mode_name_list,
                            "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                            (mode.name, mode_name), FileName, LineN)

        that_mode = blackboard.mode_db[mode_name]

        # Other mode allows all entries => don't worry.
        if len(that_mode.entry_mode_name_list) == 0: continue

        # Other mode restricts the entries from other modes
        # => check if this mode or one of the base modes can enter
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in that_mode.entry_mode_name_list: break
        else:
            error_msg("Mode '%s' has an exit to mode '%s' but" % (mode.name, mode_name),
                      FileName, LineN, DontExitF=True, WarningF=False)
            error_msg("mode '%s' has no entry for mode '%s'\n" % (mode_name, mode.name) + \
                      "or any of its base modes.",
                      that_mode.sr.file_name, that_mode.sr.line_n)

    for mode_name in mode.entry_mode_name_list:
        # Does that mode exist?
        verify_word_in_list(mode_name, mode_name_list,
                            "Mode '%s' allows entry from\nmode '%s' but no such mode exists." % \
                            (mode.name, mode_name), FileName, LineN)

        that_mode = blackboard.mode_db[mode_name]
        # Other mode allows all exits => don't worry.
        if len(that_mode.exit_mode_name_list) == 0: continue

        # Other mode restricts the exits to other modes
        # => check if this mode or one of the base modes can be reached
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in that_mode.exit_mode_name_list: break
        else:
            error_msg("Mode '%s' has an entry for mode '%s' but" % (mode.name, mode_name),
                      FileName, LineN, DontExitF=True, WarningF=False)
            error_msg("mode '%s' has no exit to mode '%s'\n" % (mode_name, mode.name) + \
                      "or any of its base modes.",
                      that_mode.sr.file_name, that_mode.sr.line_n)
           
def __get_non_abstract_mode_name_list(ModeDB):
    return result
