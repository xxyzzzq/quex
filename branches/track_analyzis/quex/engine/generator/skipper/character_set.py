import quex.engine.state_machine.index                    as     sm_index
import quex.engine.generator.state_coder.transition_block as     transition_block
from   quex.engine.generator.languages.address            import get_label, get_address
import quex.engine.generator.languages.variable_db        as     variable_db
from   quex.engine.generator.skipper.common               import *
from   quex.engine.state_machine.transition_map           import TransitionMap 
from   quex.engine.state_machine.state_core_info          import EngineTypes 
from   quex.blackboard                                    import setup as Setup
from   quex.engine.misc.string_handling                   import blue_print

def do(Data):
    LanguageDB   = Setup.language_db

    code_str, db = get_skipper(Data["character_set"])   

    txt = []
    txt.append("    ")
    txt.append(LanguageDB["$comment"]("Character set skipper state"))
    txt.extend(code_str)

    return txt, db

prolog_txt = """
    $$DELIMITER_COMMENT$$
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

    /* NOTE: For simple skippers the end of content does not have to be overwriten 
     *       with anything (as done for range skippers). This is so, because the abort
     *       criteria is that a character occurs which does not belong to the trigger 
     *       set. The BufferLimitCode, though, does never belong to any trigger set and
     *       thus, no special character is to be set.                                   */
STATE_$$SKIPPER_INDEX$$_LOOP:
    $$INPUT_GET$$ 
$$LC_COUNT_IN_LOOP$$
"""

epilog_txt = """
/* $$DROP_OUT_DIRECT$$ */
$$LC_COUNT_END_PROCEDURE$$
    /* There was no buffer limit code, so no end of buffer or end of file --> continue analysis 
     * The character we just swallowed must be re-considered by the main state machine.
     * But, note that the initial state does not increment '_input_p'!
     */
    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
    goto $$GOTO_START$$;

$$LOOP_REENTRANCE$$:
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    goto STATE_$$SKIPPER_INDEX$$_LOOP;

$$RELOAD$$:
    /* -- When loading new content it is always taken care that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                   
     * -- The input_p will at this point in time always point to the buffer border.        */
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
$$LC_COUNT_BEFORE_RELOAD$$
        $$MARK_LEXEME_START$$
        if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
            goto $$GOTO_TERMINAL_EOF$$;
        } else {
            QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)position, PositionRegisterN);

            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
$$LC_COUNT_AFTER_RELOAD$$
            goto STATE_$$SKIPPER_INDEX$$_LOOP;
        } 
    }
"""

def get_skipper(TriggerSet):
    """This function implements simple 'skipping' in the sense of passing by
       characters that belong to a given set of characters--the TriggerSet.
    """
    global template_str
    assert TriggerSet.__class__.__name__ == "NumberSet"
    assert not TriggerSet.is_empty()

    LanguageDB = Setup.language_db

    skipper_index = sm_index.get()
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.
    transition_map = TransitionMap() # (don't worry about 'drop-out-ranges' etc.)
    transition_map.add_transition(TriggerSet, skipper_index)
    # On buffer limit code, the skipper must transit to a dedicated reloader

    iteration_code = []
    transition_block.do(iteration_code, 
                        transition_map.get_trigger_map(), 
                        skipper_index, 
                        EngineTypes.ELSE,
                        GotoReload_Str="goto %s;" % get_label("$reload", skipper_index))

    comment_str = LanguageDB["$comment"]("Skip any character in " + TriggerSet.get_utf8_string())

    # Line and column number counting
    prolog = __lc_counting_replacements(prolog_txt, TriggerSet)
    epilog = __lc_counting_replacements(epilog_txt, TriggerSet)

    prolog = blue_print(prolog,
                        [
                         ["$$DELIMITER_COMMENT$$",              comment_str],
                         ["$$SKIPPER_INDEX$$",                  "%i" % skipper_index],
                         ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                        ])

    epilog = blue_print(epilog,
                        [
                         ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                         ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                         ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("SkipDelimiter$$SKIPPER_INDEX$$[0]")],
                         ["$$ENDIF$$",                          LanguageDB["$endif"]],
                         ["$$LOOP_REENTRANCE$$",                get_label("$entry", skipper_index)],
                         ["$$INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB["$BLC"]],
                         ["$$RELOAD$$",                         get_label("$reload", skipper_index)],
                         ["$$DROP_OUT_DIRECT$$",                get_label("$drop-out", skipper_index, U=True)],
                         ["$$SKIPPER_INDEX$$",                  "%i" % skipper_index],
                         ["$$LABEL_TERMINAL_EOF$$",             "QUEX_LABEL(%i)" % get_address("$terminal-EOF", U=True)],
                         ["$$LABEL_REF_AFTER_RELOAD$$",         "QUEX_LABEL(%i)" % get_address("$skipper-reload", skipper_index, U=True)],
                         ["$$GOTO_TERMINAL_EOF$$",              get_label("$terminal-EOF", U=True)],
                         ["$$LABEL_AFTER_RELOAD$$",             get_label("$skipper-reload", skipper_index)],
                         # When things were skipped, no change to acceptance flags or modes has
                         # happend. One can jump immediately to the start without re-entry preparation.
                         ["$$GOTO_START$$",                     get_label("$start", U=True)], 
                         ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                        ])

    code = [ prolog ]
    code.extend(iteration_code)
    code.append(epilog)

    local_variable_db = {}
    variable_db.enter(local_variable_db, "reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")

    return code, local_variable_db

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
    variable_definition = "    __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"

    in_loop       = ""
    # Does the end delimiter contain a newline?
    if CharacterSet.contains(ord("\n")): in_loop = line_column_counter_in_loop

    end_procedure = "        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(me->buffer._input_p - reference_p));\n" 
    before_reload  = "       __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(me->buffer._input_p - reference_p));\n" 
    after_reload   = "           __QUEX_IF_COUNT_COLUMNS(reference_p = me->buffer._input_p);\n" 

    return blue_print(code_str,
                     [["$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$", variable_definition],
                      ["$$LC_COUNT_IN_LOOP$$",                     in_loop],
                      ["$$LC_COUNT_END_PROCEDURE$$",               end_procedure],
                      ["$$LC_COUNT_BEFORE_RELOAD$$",               before_reload],
                      ["$$LC_COUNT_AFTER_RELOAD$$",                after_reload],
                      ])
