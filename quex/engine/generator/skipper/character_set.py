import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.transition_map          as     transition_map_tools
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.entry_action      import DoorID
import quex.engine.generator.state.transition.core  as     transition_block
from   quex.engine.generator.state.transition.code  import TextTransitionCode
from   quex.engine.generator.languages.address      import get_label, \
                                                           get_address, \
                                                           address_set_subject_to_routing_add
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.skipper.common         import line_column_counter_in_loop
import quex.output.cpp.counter                      as     counter
from   quex.blackboard                              import E_StateIndices, setup as Setup
from   quex.engine.misc.string_handling             import blue_print
from   quex.engine.interval_handling                import NumberSet, Interval

import quex.engine.tools             as tools

OnBufferLimitCode = "<<__dummy__OnBufferLimitCode__>>" 
OnExitCharacter   = "<<__dummy__OnExitCharacter__>>" 

def do(Data, Mode):
    """________________________________________________________________________
    Generate a character set skipper state. As long as characters of a given
    character set appears it iterates to itself.
    ___________________________________________________________________________
    """
    global OnExitCharacter
    global OnBufferLimitCode

    # tools.print_callstack()

    LanguageDB   = Setup.language_db
    CharacterSet = Data["character_set"]
    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()
    require_label_SKIP_f = Data["require_label_SKIP_f"]
    assert type(require_label_SKIP_f) == bool


    column_count_per_chunk = counter.get_column_number_per_chunk(Mode.counter_db, CharacterSet)
    reference_p_approach_f = column_count_per_chunk is not None
    if reference_p_approach_f:
        reference_p_exception_set = counter.get_grid_and_line_number_character_set(Mode.counter_db)
    else:
        reference_p_exception_set = None

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    skipper_adr = sm_index.get()
    address_set_subject_to_routing_add(skipper_adr) # Mark as 'used'

    get_label("$state-router", U=True)  # 'reload' requires state router

    # Possible reactions on a character _______________________________________
    #
    action_db = []
   
    # --  Return to loop start (while character in in set to be skipped)
    #
    #     This is generated completely by the counter implementer. 
    #
    action_db.append((CharacterSet, None))

    # --  Reload (on 'buffer limit code', which cannot be skipped)
    #
    action_db.append((NumberSet(Setup.buffer_limit_code), [OnBufferLimitCode]))

    # --  Exit the loop.
    #
    inverse_character_set = CharacterSet.inverse()
    inverse_character_set.subtract(Interval(Setup.buffer_limit_code))
    action_db.append((inverse_character_set, [OnExitCharacter]))

    # Build the skipper _______________________________________________________
    #
    column_counter_per_chunk, state_machine_f, tm = \
            counter.get_transition_map(Mode.counter_db, action_db, None, "me->buffer._input_p")

    __insert_actions(tm, reference_p_exception_set, column_counter_per_chunk, skipper_adr)

    dummy, txt = counter.get_core_step(tm, "me->buffer._input_p", state_machine_f)

    return __frame(txt, CharacterSet, skipper_adr, reference_p_approach_f, require_label_SKIP_f)

def __frame(Txt, CharacterSet, SkipperAdr, ReferenceP_F, RequireLabelSKIP_F):
    LanguageDB = Setup.language_db

    # (*) Compose
    code =  []

    code.append("__SKIP:\n")
    code.append(1)

    LanguageDB.COMMENT(code, "Character Set Skipper: %s" % CharacterSet.get_utf8_string()),
    code.append(1)
    code.append("QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);\n")

    if ReferenceP_F:
        code.append(1)
        LanguageDB.REFERENCE_P_RESET(code, "me->buffer._input_p", AddOneF=False)

    code.append(1)
    code.append("while( 1 + 1 == 2 ) {\n")
    code.append(1)

    LanguageDB.INDENT(Txt)
    code.extend(Txt)

    code.extend([
        1, "}\n",
        1, "__quex_assert_no_passage();\n",
        "%s:\n" % LanguageDB.ADDRESS_LABEL(SkipperAdr), 
        1, "%s\n" % LanguageDB.INPUT_P_INCREMENT(),
        1, "goto __SKIP;\n"
    ])

    if ReferenceP_F:
        variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return code

def __insert_actions(tm, ReferenceP_ExceptionSet, ColumnCountPerChunk, UponReloadDoneAdr):
    global OnExitCharacter
    global OnBufferLimitCode

    for i, info in enumerate(tm):
        interval, action_list = info
        if   len(action_list) != 0 and action_list[-1] == OnExitCharacter:
            del action_list[:]
            __add_on_exit_character(interval, action_list, 
                                    ReferenceP_ExceptionSet, ColumnCountPerChunk)

        elif len(action_list) != 0 and action_list[-1] == OnBufferLimitCode:
            __add_on_buffer_limit_code(interval, action_list, 
                                       ReferenceP_ExceptionSet, ColumnCountPerChunk, UponReloadDoneAdr)

def __add_on_buffer_limit_code(TheInterval, txt, ReferenceP_ExceptionSet, ColumnCountPerChunk, UponReloadDoneAdr):
    LanguageDB = Setup.language_db

    del txt[-1]
    if         ReferenceP_ExceptionSet is not None \
       and not ReferenceP_ExceptionSet.has_intersection(TheInterval):
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, "me->buffer._input_p", ColumnCountPerChunk)
        txt.append(0)

    txt.extend([
        "%s\n" % LanguageDB.LEXEME_START_SET(),
        # InitStateF=True causes transition to EndOfStream handler upon reload failure.
        "%s\n" % LanguageDB.GOTO_RELOAD(UponReloadDoneAdr, True, engine.FORWARD)
    ])

def __add_on_exit_character(TheInterval, txt, ReferenceP_ExceptionSet, ColumnCountPerChunk):
    LanguageDB = Setup.language_db

    if         ReferenceP_ExceptionSet is not None \
       and not ReferenceP_ExceptionSet.has_intersection(TheInterval):
        LanguageDB.REFERENCE_P_COLUMN_ADD(txt, "me->buffer._input_p", ColumnCountPerChunk)
        txt.append(0)
    txt.append("goto %s;" % get_label("$start", U=True))

