import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.transition_map          as     transition_map_tools
from   quex.engine.analyzer.state.entry_action      import DoorID
import quex.engine.generator.state.transition.core  as     transition_block
from   quex.engine.generator.state.transition.code  import TextTransitionCode
from   quex.engine.generator.languages.address      import get_label, get_address
import quex.engine.generator.languages.variable_db  as     variable_db
from   quex.engine.generator.skipper.common         import line_column_counter_in_loop
from   quex.blackboard                              import E_EngineTypes, E_StateIndices, setup as Setup
from   quex.engine.misc.string_handling             import blue_print

def do(Data):
    """________________________________________________________________________
    Generate a character set skipper state. As long as characters of a given
    character set appears it iterates to itself.
    ___________________________________________________________________________
    """
    LanguageDB   = Setup.language_db
    CharacterSet = Data["character_set"]
    assert CharacterSet.__class__.__name__ == "NumberSet"
    assert not CharacterSet.is_empty()

    LanguageDB     = Setup.language_db

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    skipper_adr     = sm_index.get()
    skipper_label   = LanguageDB.ADDRESS_LABEL(skipper_adr)
    skipper_adr_str = "%i" % skipper_adr

    upon_reload_done_adr     = sm_index.get()
    upon_reload_done_label   = LanguageDB.ADDRESS_LABEL(upon_reload_done_label)
    upon_reload_done_adr_str = "%i" % upon_reload_done_adr

    transition_block_str = __get_transition_block(CharacterSet, skipper_adr)

    # Line and column number counting
    prolog = __lc_counting_replacements(prolog_txt, CharacterSet)
    prolog = blue_print(prolog,
                        [
                         ["$$DELIMITER_COMMENT$$",      CharacterSet.get_utf8_string()],
                         ["$$LABEL$$",                  skipper_label], 
                         ["$$ADDRESS$$",                skipper_adr_str], 
                         ["$$INPUT_GET$$",              LanguageDB.ACCESS_INPUT()],
                         ["$$INPUT_P_INCREMENT$$",      LanguageDB.INPUT_P_INCREMENT()],
                         ["$$UPON_RELOAD_DONE_LABEL$$", upon_reload_done_label],
                        ])

    epilog = __lc_counting_replacements(epilog_txt, CharacterSet)
    epilog = blue_print(epilog,
                        [
                         ["$$BUFFER_LIMIT_CODE$$",     LanguageDB.BUFFER_LIMIT_CODE],
                         ["$$ADDRESS$$",           skipper_adr_str], 
                         ["$$TERMINAL_EOF_ADR$$",      "%i" % get_address("$terminal-EOF", U=True)],
                         ["$$REENTRY$$",               get_label("$start", U=True)], 
                         ["$$MARK_LEXEME_START$$",     LanguageDB.LEXEME_START_SET()],
                         ["$$UPON_RELOAD_DONE_ADR$$",  upon_reload_done_adr_str],
                        ])

    code = [ prolog ]
    code.extend(transition_block_str)
    code.append(epilog)

    local_variable_db = {}
    variable_db.enter(local_variable_db, "reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    # Mark as 'used'
    get_label("$state-router", U=True)  # 'reload' requires state router
    get_address("$entry", upon_reload_done_adr) # 

    return code, local_variable_db

prolog_txt = """
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

    /* Character Set Skipper: $$DELIMITER_COMMENT$$ */
    __QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);

    goto _ENTRY_$$ADDRESS$$;

$$UPON_RELOAD_DONE_LABEL$$: /* Upon 'reload done' */
    __QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p + 1);
$$LABEL$$: /* Skipper state's loop entry */      
    $$INPUT_P_INCREMENT$$
_ENTRY_$$ADDRESS$$: /* First entry into skipper state */
$$INPUT_GET$$$$LC_COUNT_IN_LOOP$$
"""

epilog_txt = """$$LC_COUNT_END_PROCEDURE$$
    /* There was no buffer limit code, so no end of buffer or end of file --> continue analysis 
     * The character we just swallowed must be re-considered by the main state machine.
     * But, note that the initial state does not increment '_input_p'!
     *
     * No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
    goto $$REENTRY$$;

_RELOAD_$$ADDRESS$$:
    /* -- When loading new content it is always taken care that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                   
     * -- The input_p will at this point in time always point to the buffer border.        */
    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(me->buffer._input_p - reference_p));
    $$MARK_LEXEME_START$$
    QUEX_GOTO_RELOAD_FORWARD($$UPON_RELOAD_DONE_ADR$$, $$TERMINAL_EOF_ADR$$);
"""

def __lc_counting_replacements(code_str, CharacterSet):
    """Line and Column Number Counting(Range Skipper):
     
         -- in loop if there appears a newline, then do:
            increment line_n
            set position from where to count column_n
         -- at end of skipping do one of the following:
            if end delimiter contains newline:
               column_n = number of letters since last new line in end delimiter
               increment line_n by number of newlines in end delimiter.
               (NOTE: in this case the setting of the position from where to count
                      the column_n can be omitted.)
            else:
               column_n = current_position - position from where to count column number.

       NOTE: On reload we do count the column numbers and reset the column_p.
    """
    in_loop = ""
    # Does the end delimiter contain a newline?
    if CharacterSet.contains(ord("\n")): in_loop = line_column_counter_in_loop()

    end_procedure = "    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(me->buffer._input_p - reference_p));\n" 

    return blue_print(code_str,
                     [
                      ["$$LC_COUNT_IN_LOOP$$",       in_loop],
                      ["$$LC_COUNT_END_PROCEDURE$$", end_procedure],
                      ])

def __get_transition_block(CharacterSet, SkipperAdr):
    """Generate the transition block.
    
    The transition code MUST circumvent the 'TransitionID --> DoorID' mapping.
    This is so, since the implemented state is not 'officially' part of the
    analyzer state machine. The transition_map relies on 'TextTransitionCode'
    objects as target.
    """
    LanguageDB = Setup.language_db

    def extend(transition_map, character_set, Target):
        interval_list = character_set.get_intervals(PromiseToTreatWellF=True)
        transition_map.extend((interval, Target) for interval in interval_list)

    # Circumvent the State-DoorID mechanism by providing TextTransitionCode objects
    # in the transition map. Those are not subject to 'transition_id->door_id'
    # mapping.
    transition_map = []
    extend(transition_map, CharacterSet, 
           TextTransitionCode(LanguageDB.GOTO_ADDRESS(SkipperAdr)))

    # 'CharacterSet.get_intervals()' returned a sorted list.
    # => transition_map_tools.sort() not necessary, 
    transition_map_tools.fill_gaps(transition_map, E_StateIndices.DROP_OUT)

    txt = []
    transition_block.do(txt, transition_map, 
                        SkipperAdr, 
                        E_EngineTypes.ELSE,
                        GotoReload_Str="goto _RELOAD_%s;" % SkipperAdr)
    return txt

