import quex.engine.misc.error                      as     error
from   quex.input.setup                            import NotificationDB
import quex.blackboard                             as     blackboard
from   quex.blackboard                             import setup as Setup
from   quex.blackboard import E_IncidenceIDs

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
            error.log("Modes found in input files. However, only a token class is generated.", 
                      DontExitF=True)
        return

    if len(ModeDB) == 0:
        error.log("No single mode defined - bailing out", Prefix="consistency check")

    mode_name_list             = sorted([mode.name for mode in ModeDB.itervalues()]) 
    # Applicable modes can only be determined after possible addition of "inheritable: only"
    implemented_mode_name_list = sorted([mode.name for mode in ModeDB.itervalues() if not mode.abstract_f()]) 

    if len(implemented_mode_name_list) == 0:
        error.log("There is no mode that can be implemented---all existing modes are 'inheritable only'.\n" + \
                  "modes are = " + repr(ModeDB.keys())[1:-1],
                  Prefix="consistency check")

    for mode in ModeDB.values():
        mode.check_consistency()

    # (*) If a conversion or a codec engine is specified, then the 
    #     'on_bad_lexatom' handler must be specified in every mode.
    if False and (Setup.buffer_codec.name != "unicode" or Setup.converter_f):
        for mode in ModeDB.values():
            # Later ... 
            if False and E_IncidenceIDs.CODEC_ERROR not in mode.incidence_db:
                error.warning("Missing 'on_bad_lexatom' handler in mode '%s' (or its base modes).\n" % mode.name + \
                              "This is dangerous while using a codec engine or a converter (iconv, icu, ...).\n" + \
                              "The feature is not yet supported, but the infrastructure is currently setup for it.",
                              mode.sr, 
                              SuppressCode=NotificationDB.warning_codec_error_with_non_unicode)

    # (*) Start mode specified?
    __start_mode(implemented_mode_name_list, mode_name_list)

    # (*) Entry/Exit Transitions
    for mode in ModeDB.values():
        if mode.abstract_f(): continue
        __entry_transitions(mode, mode_name_list)
        __exit_transitions(mode, mode_name_list)

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
    
    error.log("The pattern '%s' %s" % (This.pattern_string(), ThisComment), 
              This.sr, DontExitF=True, WarningF=not ExitF)

    msg = "pattern '%s'." % That.pattern_string()

    if len(EndComment) == 0:
        error.log(msg, That.sr, DontExitF=not ExitF, WarningF=not ExitF, 
                  SuppressCode=SuppressCode)
    else:
        error.log(msg,        That.sr, DontExitF=True,      WarningF=not ExitF)
        error.log(EndComment, That.sr, DontExitF=not ExitF, WarningF=not ExitF, 
                  SuppressCode=SuppressCode)

def __start_mode(implemented_mode_name_list, mode_name_list):
    """If more then one mode is defined, then that requires an explicit 
       definition 'start = mode'.
    """
    assert len(implemented_mode_name_list) != 0

    assert blackboard.initial_mode is not None

    start_mode = blackboard.initial_mode.get_pure_text()

    # Start mode present and applicable?
    error.verify_word_in_list(start_mode, mode_name_list,
                        "Start mode '%s' is not defined." % start_mode,
                        blackboard.initial_mode.sr)
    error.verify_word_in_list(start_mode, implemented_mode_name_list,
                        "Start mode '%s' is inheritable only and cannot be instantiated." % start_mode,
                        blackboard.initial_mode.sr)

def __access_mode(Mode, OtherModeName, ModeNameList, EntryF):
    type_str = { True: "entry from", False: "exit to" }[EntryF]

    error.verify_word_in_list(OtherModeName, ModeNameList,
              "Mode '%s' permits the %s mode '%s'\nbut no such mode exists." % \
              (Mode.name, type_str, OtherModeName), Mode.sr)
    result = blackboard.mode_db[OtherModeName]
    assert result is not None
    return result

def __error_transition(Mode, OtherMode, EntryF):
    type_str  = { True: "entry",      False: "exit" }[EntryF]
    type0_str = { True: "entry from", False: "exit to" }[EntryF]
    type1_str = { True: "exit to",    False: "entry from" }[EntryF]

    error.log("Mode '%s' permits the %s mode '%s' but mode '%s' does not" % (Mode.name, type0_str, OtherMode.name, OtherMode.name),
              Mode.sr, DontExitF=True)
    error.log("permit the %s mode '%s' or any of its base modes." % (type1_str, Mode.name),
              OtherMode.sr, DontExitF=True)
    error.log("May be, use explicitly mode tag '<%s: ...>' for restriction." % type_str, 
              Mode.sr)

def __exit_transitions(mode, mode_name_list):
    for exit_mode_name in mode.exit_mode_name_list:
        exit_mode = __access_mode(mode, exit_mode_name, mode_name_list, EntryF=False)

        # Check if this mode or one of the base modes can enter
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in exit_mode.entry_mode_name_list: break
        else:
            __error_transition(mode, exit_mode, EntryF=False)

def __entry_transitions(mode, mode_name_list):
    for entry_mode_name in mode.entry_mode_name_list:
        entry_mode = __access_mode(mode, entry_mode_name, mode_name_list, EntryF=True)

        # Check if this mode or one of the base modes can be reached
        for base_mode in mode.get_base_mode_sequence():
            if base_mode.name in entry_mode.exit_mode_name_list: break
        else:
            __error_transition(mode, entry_mode, EntryF=True)
           
