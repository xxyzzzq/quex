import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.generator.base                   import Generator as CppGenerator
from   quex.engine.generator.languages.address      import get_label, \
                                                           address_set_subject_to_routing_add
from   quex.engine.generator.languages.variable_db  import variable_db
import quex.output.cpp.counter                      as     counter
from   quex.blackboard                              import setup as Setup, \
                                                           E_StateIndices
from   quex.engine.interval_handling                import NumberSet, Interval
import quex.engine.analyzer.transition_map          as     transition_map_tool

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
    # tools.print_callstack()

    CharacterSet         = Data["character_set"]
    require_label_SKIP_f = Data["require_label_SKIP_f"]

    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()
    assert type(require_label_SKIP_f) == bool

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    get_label("$state-router", U=True)                       # 'reload' req. state router

    # Implement the core loop _________________________________________________
    #
    loop_txt,               \
    reference_p_required_f, \
    state_machine_f,        \
    upon_reload_done_adr    = __make_loop(Mode, CharacterSet)

    # Build the skipper _______________________________________________________
    #
    result = __frame(loop_txt, CharacterSet, reference_p_required_f, state_machine_f, 
                     upon_reload_done_adr, require_label_SKIP_f)

    # Require the 'reference_p' variable to be defined, if necessary __________
    #
    if reference_p_required_f:
        variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return result

def __make_loop(Mode, CharacterSet):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    LanguageDB = Setup.language_db

    # Determine 'column_count_per_chunk' before adding 'exit' and 'blc' 
    # characters.
    column_count_per_chunk = counter.get_column_number_per_chunk(Mode.counter_db, CharacterSet)
    reference_p_required_f = column_count_per_chunk is not None

    # Possible reactions on a character _______________________________________
    #
    blc_set       = NumberSet(Setup.buffer_limit_code)
    skip_set      = CharacterSet.clone()
    skip_set.subtract(blc_set)
    exit_skip_set = CharacterSet.inverse()
    exit_skip_set.subtract(blc_set)

    #  Buffer Limit Code --> Reload
    #  Skip Character    --> Loop to Skipper State
    #  Else              --> Exit Loop

    # Implement the core loop _________________________________________________
    # 'column_count_per_chunk' is ignored, because it contains considerations
    # of BLC and 'exit' character.
    tm, column_count_per_chunk = \
         counter.get_counter_map(Mode.counter_db, 
                                 IteratorName             = "me->buffer._input_p",
                                 ColumnCountPerChunk      = column_count_per_chunk,
                                 ConcernedCharacterSet    = CharacterSet,
                                 DoNotResetReferenceP_Set = exit_skip_set)
                                 ActionEpilog             = ["continue;\n"]) 

    tm = add_on_exit_actions(tm, exit_skip_set, column_count_per_chunk)

    # Prepare reload procedure, ensure transition to 'drop-out'
    transition_map_tool.set(tm, Setup.buffer_limit_code, E_StateIndices.DROP_OUT)
    before_reload_action = get_before_reload_actions(column_count_per_chunk)

    # 'BeforeReloadAction not None' forces a transition to RELOAD_PROCEDURE upon
    # buffer limit code.
    state_machine_f,     \
    txt,                 \
    upon_reload_done_adr = CppGenerator.code_action_map(tm, 
                                        IteratorName       = "me->buffer._input_p", 
                                        BeforeReloadAction = before_reload_action, 
                                        OnFailureAction    = None)

    return txt, column_count_per_chunk, state_machine_f, upon_reload_done_adr

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
    exit_action = []
    if Setup.variable_character_sizes_f():
        # Here, characters are made up of more than one 'chunk'. When the last
        # character needs to be reset, its start position must be known. For 
        # this the 'lexeme start pointer' is used.
        exit_action.extend([1, "%s\n" % LanguageDB.INPUT_P_TO_LEXEME_START()])
    exit_action.extend(["goto %s;" % get_label("$start", U=True)])

    exit_tm = get_transition_map(exit_action, ExitSkipSet)

    return transition_map_tool.add_transition_actions(tm, exit_tm)

def get_before_reload_actions(ColumnCountPerChunk):
    LanguageDB = Setup.language_db
    result = []
    if ColumnCountPerChunk is not None:
        LanguageDB.REFERENCE_P_COLUMN_ADD(result, "me->buffer._input_p", ColumnCountPerChunk)

    if not Setup.variable_character_sizes_f():
        # If there are variable size characters, then the lexeme start
        # pointer points to the begin of the current character. Thus, it
        # cannot be reset.
        result.append("%s\n" % LanguageDB.LEXEME_START_SET())

    return result

def __frame(LoopTxt, CharacterSet, ReferenceP_F, StateMachineF, UponReloadDoneAdr, SkipLabelRequiredF):
    """Implement the skipper."""
    LanguageDB = Setup.language_db

    # (*) Rules _______________________________________________________________
    if ReferenceP_F:
        reference_p_reset = [ 1 ]
        LanguageDB.REFERENCE_P_RESET(reference_p_reset, "me->buffer._input_p", AddOneF=False)
    else:
        reference_p_reset = []

    if (not StateMachineF) or SkipLabelRequiredF:
        skipper_entry_label = "__SKIP:\n"
    else:
        skipper_entry_label = ""

    if not StateMachineF:
        upon_reload_done    = []
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
        # State machine based counters cannot have a fixed 'column_count_per_chunk'.
        # Thus, they do not need a reference pointer.
        assert len(reference_p_reset) == 0
        upon_reload_done    = []

    if Setup.variable_character_sizes_f():
        assert StateMachineF
        # Here, characters are made up of more than one 'chunk'. When the last
        # character needs to be reset, its start position must be known. For 
        # this the 'lexeme start pointer' is used.
        loop_epilog = [1, "%s\n" % LanguageDB.LEXEME_START_SET()]
    else:
        loop_epilog = []

    comment = [1]
    LanguageDB.COMMENT(comment, "Character Set Skipper: '%s'" % CharacterSet.get_utf8_string()),
    LanguageDB.INDENT(LoopTxt)

    # (*) Putting it all together _____________________________________________
    code = [ skipper_entry_label ]
    code.extend(comment)
    code.extend([1, "QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n"])
    code.extend(reference_p_reset)
    code.extend([ 1, "while( 1 + 1 == 2 ) {\n" ])
    code.extend(loop_epilog)
    code.extend(LoopTxt)
    code.extend([ 1, "}\n"])
    code.extend(upon_reload_done)

    return code

