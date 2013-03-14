import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.generator.languages.address      import get_label, \
                                                           address_set_subject_to_routing_add
from   quex.engine.generator.languages.variable_db  import variable_db
import quex.output.cpp.counter                      as     counter
from   quex.blackboard                              import setup as Setup
from   quex.engine.interval_handling                import NumberSet, Interval
import quex.engine.analyzer.transition_map          as     transition_map_tool

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

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    skipper_adr = sm_index.get()
    address_set_subject_to_routing_add(skipper_adr) # Mark as 'used'
    get_label("$state-router", U=True)              # 'reload' req. state router

    # Implement the core loop _________________________________________________
    #
    core_txt, reference_p_required_f = __core(Mode, CharacterSet, skipper_adr)

    # Build the skipper _______________________________________________________
    #
    if reference_p_required_f:
        variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return __frame(core_txt, CharacterSet, reference_p_required_f, skipper_adr)

def __core(Mode, CharacterSet, UponReloadDoneAdr):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    # Determine 'column_count_per_chunk' before adding 'exit' and 'blc' 
    # characters.
    column_count_per_chunk = counter.get_column_number_per_chunk(Mode.counter_db, CharacterSet)
    reference_p_required_f = column_count_per_chunk is not None

    # Possible reactions on a character _______________________________________
    #
    blc_set                = NumberSet(Setup.buffer_limit_code)
    skip_set               = CharacterSet.clone()
    skip_set.subtract(blc_set)
    exit_skip_set = CharacterSet.inverse()
    exit_skip_set.subtract(blc_set)

    #  Buffer Limit Code --> Reload
    #  Skip Character    --> Loop to Skipper State
    #  Else              --> Exit Loop

    # Implement the core loop _________________________________________________
    # 'column_count_per_chunk' is ignored, because it contains considerations
    # of BLC and 'exit' character.
    tm, column_count_per_chunk, state_machine_f = \
         counter.get_counter_map(Mode.counter_db, 
                                 IteratorName        = "me->buffer._input_p",
                                 Trafo               = Setup.buffer_codec_transformation_info,
                                 ColumnCountPerChunk = column_count_per_chunk)

    add_on_exit_actions(tm, exit_skip_set, column_count_per_chunk)

    dummy, txt = counter.get_core_step(tm, "me->buffer._input_p", state_machine_f, 
                                       BeforeGotoReloadAction = before_reload_actions(column_count_per_chunk))

    return txt, column_count_per_chunk

def add_on_exit_actions(tm, ExitSkipSet, ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    # Depending on whether the column number add can be computed from lexeme
    # length, a '(iterator - reference_p) * C' must be done.
    on_exit = []
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(on_exit, "me->buffer._input_p", ColumnCountPerChunk)
    on_exit.append("goto %s;" % get_label("$start", U=True))

    # The exit action is performed upon the characters which are not to be 
    # skipped. 
    exit_tm = [
        (interval, on_exit) 
        for interval in ExitSkipSet.get_intervals(PromiseToTreatWellF=True)
    ]

    # Before the content of transition maps can be added, the gaps need to be 
    # filled.
    transition_map_tool.fill_gaps(tm, [])
    transition_map_tool.fill_gaps(exit_tm, [])
    transition_map_tool.add_transition_actions(tm, exit_tm)

def before_reload_actions(ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    result = []
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(result, "me->buffer._input_p", ColumnCountPerChunk)

    result.append("%s\n" % LanguageDB.LEXEME_START_SET())

    return result

def __frame(Txt, CharacterSet, ReferenceP_F, SkipperAdr):
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

    return code

