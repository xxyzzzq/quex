import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.generator.languages.address      import get_label, \
                                                           address_set_subject_to_routing_add
from   quex.engine.generator.languages.variable_db  import variable_db
import quex.output.cpp.counter                      as     counter
from   quex.blackboard                              import setup as Setup
from   quex.engine.interval_handling                import NumberSet, Interval

OnBufferLimitCode = "<<__dummy__OnBufferLimitCode__>>" 
OnExitCharacter   = "<<__dummy__OnExitCharacter__>>" 

def do(Data, Mode):
    """________________________________________________________________________
    Generate a character set skipper state. As long as characters of a given
    character set appears it iterates to itself:

                                 input in Set
                                   .--<---.
                                  |       |
                              .-------.   |
                   --------->( SKIPPER )--+----->------> RESTART
                              '-------'       input 
                                            not in Set
    ___________________________________________________________________________
    """
    global OnExitCharacter
    global OnBufferLimitCode

    # tools.print_callstack()

    CharacterSet         = Data["character_set"]
    require_label_SKIP_f = Data["require_label_SKIP_f"]

    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()
    assert type(require_label_SKIP_f) == bool


    column_count_per_chunk = counter.get_column_number_per_chunk(Mode.counter_db, CharacterSet)
    reference_p_required_f = column_count_per_chunk is not None

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    skipper_adr = sm_index.get()
    address_set_subject_to_routing_add(skipper_adr) # Mark as 'used'
    get_label("$state-router", U=True)              # 'reload' req. state router

    # Possible reactions on a character _______________________________________
    #
    action_db = []
   
    blc_set                = NumberSet(Setup.buffer_limit_code)
    skip_set               = CharacterSet.clone()
    skip_set.subtract(blc_set)
    complementary_skip_set = CharacterSet.inverse()
    complementary_skip_set.subtract(blc_set)

    #  Buffer Limit Code --> Reload
    #  Skip Character    --> Loop to Skipper State
    #  Else              --> Exit Loop
    action_db.append((blc_set,                [OnBufferLimitCode]))
    action_db.append((skip_set,               None))
    action_db.append((complementary_skip_set, [OnExitCharacter]))

    # Build the skipper _______________________________________________________
    #
    column_counter_per_chunk, state_machine_f, tm = \
            counter.get_transition_map(Mode.counter_db, action_db, None, "me->buffer._input_p")

    __insert_actions(tm,  reference_p_required_f, column_counter_per_chunk, skipper_adr)

    dummy, txt = counter.get_core_step(tm, "me->buffer._input_p", state_machine_f)

    return __frame(txt, CharacterSet, skipper_adr, reference_p_required_f, require_label_SKIP_f)

def __frame(Txt, CharacterSet, SkipperAdr, ReferenceP_F, RequireLabelSKIP_F):
    """Implement the skipper."""
    LanguageDB = Setup.language_db
    LanguageDB.INDENT(Txt)

    code = []

    code.append("__SKIP:\n")
    code.append(1)

    LanguageDB.COMMENT(code, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])

    if ReferenceP_F:
        code.append(1)
        LanguageDB.REFERENCE_P_RESET(code, "me->buffer._input_p", AddOneF=False)

    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])

    code.append(1)
    code.extend(Txt)

    code.extend([
        1, "}\n",
        1, "__quex_assert_no_passage();\n",
        "%s: /* After RELOAD */\n"   % LanguageDB.ADDRESS_LABEL(SkipperAdr), 
        1, "%s\n" % LanguageDB.INPUT_P_INCREMENT(),
        1, "goto __SKIP;\n"
    ])

    if ReferenceP_F:
        variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return code

def __insert_actions(tm, ReferenceP_F, ColumnCountPerChunk, UponReloadDoneAdr):
    global OnExitCharacter
    global OnBufferLimitCode

    # Character Set where the reference pointer needs to be reset: 
    # 'grid' and 'newline' characters.
    for i, info in enumerate(tm):
        interval, action_list = info
        if   len(action_list) != 0 and action_list[-1] == OnExitCharacter:
            del action_list[:]
            __add_on_exit_character(action_list, interval, ReferenceP_F, 
                                    ColumnCountPerChunk)

        elif len(action_list) != 0 and action_list[-1] == OnBufferLimitCode:
            del action_list[-1]
            __add_on_buffer_limit_code(action_list, interval, ReferenceP_F, 
                                       ColumnCountPerChunk, UponReloadDoneAdr)

def __add_on_exit_character(txt, TheInterval, ReferenceP_F, ColumnCountPerChunk):
    LanguageDB = Setup.language_db

    if ReferenceP_F is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, "me->buffer._input_p", ColumnCountPerChunk)

    txt.append("goto %s;" % get_label("$start", U=True))

def __add_on_buffer_limit_code(txt, TheInterval, ReferenceP_F, ColumnCountPerChunk, 
                               UponReloadDoneAdr):
    LanguageDB = Setup.language_db

    if ReferenceP_F is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, "me->buffer._input_p", ColumnCountPerChunk)

    txt.extend([
        "%s\n" % LanguageDB.LEXEME_START_SET(),
        # InitStateF=True causes transition to EndOfStream handler upon reload failure.
        "%s\n" % LanguageDB.GOTO_RELOAD(UponReloadDoneAdr, True, engine.FORWARD)
    ])


