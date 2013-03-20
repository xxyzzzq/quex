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
    upon_reload_done_adr = sm_index.get()
    address_set_subject_to_routing_add(upon_reload_done_adr) # Mark as 'used'
    get_label("$state-router", U=True)                       # 'reload' req. state router

    # Implement the core loop _________________________________________________
    #
    core_txt, reference_p_required_f, state_machine_f = __core(Mode, CharacterSet, upon_reload_done_adr)

    # Build the skipper _______________________________________________________
    #
    result = __frame(core_txt, CharacterSet, reference_p_required_f, state_machine_f, 
                     upon_reload_done_adr)

    # Require the 'reference_p' variable to be defined, if necessary __________
    #
    if reference_p_required_f:
        variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return result


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
                                 IteratorName             = "me->buffer._input_p",
                                 Trafo                    = Setup.buffer_codec_transformation_info,
                                 ColumnCountPerChunk      = column_count_per_chunk,
                                 DoNotResetReferenceP_Set = exit_skip_set)

    tm = add_on_exit_actions(tm, exit_skip_set, column_count_per_chunk)

    dummy, txt = counter.get_core_step(tm, "me->buffer._input_p", state_machine_f, 
                                       BeforeGotoReloadAction = before_reload_actions(column_count_per_chunk), 
                                       UponReloadDoneAdr      = UponReloadDoneAdr) 

    return txt, column_count_per_chunk, state_machine_f

def add_on_exit_actions(tm, ExitSkipSet, ColumnCountPerChunk):
    """When a character appears which is not to be skipped, the loop must
    be quit. The loop exit is added to the given transition map 'tm' by 
    this function. Two things need to be considered:

    (1) Every character in 'ExitSkipSet' must cause an exit of the loop.

    (2) For those characters in 'ExitSkipSet' where there is no action
        yet, it may be necessary to append a "add(iterator-reference_p)".

        This is only necessary, if the column number can be derived from
        the lexeme length. 
    """
    LanguageDB = Setup.language_db

    # Before the content of transition maps can be added, the gaps need to be 
    # filled.
    transition_map_tool.fill_gaps(tm, [])

    def get_transition_map(TheAction, ExitSkipSet):
        result = [
            (interval, TheAction) 
            for interval in ExitSkipSet.get_intervals(PromiseToTreatWellF=True)
        ]

        # Before the content of transition maps can be added, the gaps need 
        # to be filled.
        transition_map_tool.fill_gaps(result, [])

        return result

    if ColumnCountPerChunk is not None:
        # The column number add can be computed from lexeme length. Thus,
        # "add(iterator - reference_p)" is necessary.
        add_action = []
        LanguageDB.REFERENCE_P_COLUMN_ADD(add_action, "me->buffer._input_p", ColumnCountPerChunk)
        # The 'tm' has been generated to count. Thus, for regions where 'tm'
        # contains already actions, those actions contain already the
        # "add(iterator-reference_p)". The 'add' must only be put in regions
        # which are void of actions and subject to loop exit.
        add_tm = get_transition_map(add_action, ExitSkipSet)
        tm     = transition_map_tool.fill_empty_actions(tm, add_tm)

    # All characters of the 'ExitSkipSet' must trigger a loop quit.
    exit_tm = get_transition_map(["goto %s;" % get_label("$start", U=True)], 
                                 ExitSkipSet)

    return transition_map_tool.add_transition_actions(tm, exit_tm)

def before_reload_actions(ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    result = []
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(result, "me->buffer._input_p", ColumnCountPerChunk)

    result.append("%s\n" % LanguageDB.LEXEME_START_SET())

    return result

def __frame(LoopTxt, CharacterSet, ReferenceP_F, StateMachineF, UponReloadDoneAdr):
    """Implement the skipper."""
    LanguageDB = Setup.language_db

    if ReferenceP_F:
        reference_p_reset = [ 1 ]
        LanguageDB.REFERENCE_P_RESET(reference_p_reset, "me->buffer._input_p", AddOneF=False)
    else:
        reference_p_reset = []

    if not StateMachineF:
        upon_reload_done = []
        upon_reload_done.extend([
            1, "__quex_assert_no_passage();\n",
            "%s: /* After RELOAD */\n"   % LanguageDB.ADDRESS_LABEL(UponReloadDoneAdr), 
            1, "%s\n" % LanguageDB.INPUT_P_INCREMENT(),
        ])
        upon_reload_done.extend(reference_p_reset)
        upon_reload_done.extend([
            1, "goto __SKIP;\n"
        ])
    else:
        upon_reload_done = []

    comment = [1]
    LanguageDB.COMMENT(comment, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    LanguageDB.INDENT(LoopTxt)

    code = [ "__SKIP:\n" ]
    code.extend(comment)
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
    code.extend(reference_p_reset)
    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])
    code.extend(LoopTxt)
    code.extend([ 1, "}\n"])
    code.extend(upon_reload_done)

    return code

