import quex.core_engine.state_machine.index                    as     sm_index
import quex.core_engine.generator.state_coder.transition_block as     transition_block
import quex.core_engine.generator.state_coder.transition       as     transition
from   quex.core_engine.generator.skipper.common               import *
from   quex.core_engine.state_machine.transition_map           import TransitionMap 
from   quex.input.setup                                        import setup as Setup
from   quex.frs_py.string_handling                             import blue_print

def do(Data):
    LanguageDB   = Setup.language_db

    code_str, db = get_skipper(Data["character_set"])   

    txt =   "{\n"                                                 \
          + LanguageDB["$comment"]("Character set skipper state") \
          + code_str                                              \
          + "\n}\n"

    return txt, db

template_str = """
{ 
    $$DELIMITER_COMMENT$$
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);
#if 0
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        $$GOTO_RELOAD$$
    }
#endif

    /* NOTE: For simple skippers the end of content does not have to be overwriten 
     *       with anything (as done for range skippers). This is so, because the abort
     *       criteria is that a character occurs which does not belong to the trigger 
     *       set. The BufferLimitCode, though, does never belong to any trigger set and
     *       thus, no special character is to be set.                                   */
$$LOOP_START$$
    $$INPUT_GET$$ 
$$LC_COUNT_IN_LOOP$$
$$ON_TRIGGER_SET_TO_LOOP_START$$

$$DROP_OUT_DIRECT$$
$$LC_COUNT_END_PROCEDURE$$
    /* There was no buffer limit code, so no end of buffer or end of file --> continue analysis 
     * The character we just swallowed must be re-considered by the main state machine.
     * But, note that the initial state does not increment '_input_p'!
     */
    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
    $$GOTO_START$$                           

$$LOOP_REENTRANCE$$
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$GOTO_LOOP_START$$

$$RELOAD$$
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
            $$GOTO_TERMINAL_EOF$$
        } else {
            QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                                   post_context_start_position, PostContextStartPositionN);

            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
$$LC_COUNT_AFTER_RELOAD$$
            $$GOTO_LOOP_START$$
        } 
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
    iteration_code = "".join(transition_block.do(transition_map.get_trigger_map(), skipper_index, DSM=None))
    iteration_code += transition.get_transition_to_drop_out(skipper_index, ReloadF=False)

    comment_str = LanguageDB["$comment"]("Skip any character in " + TriggerSet.get_utf8_string())

    # Line and column number counting
    code_str = __lc_counting_replacements(template_str, TriggerSet)

    # The finishing touch
    txt = blue_print(code_str,
                      [
                       ["$$DELIMITER_COMMENT$$",              comment_str],
                       ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                       ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                       ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                       ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("SkipDelimiter$$SKIPPER_INDEX$$[0]")],
                       ["$$ENDIF$$",                          LanguageDB["$endif"]],
                       ["$$LOOP_START$$",                     LanguageDB["$label-def"]("$input", skipper_index)],
                       ["$$GOTO_LOOP_START$$",                LanguageDB["$goto"]("$input", skipper_index)],
                       ["$$LOOP_REENTRANCE$$",                LanguageDB["$label-def"]("$entry", skipper_index)],
                       ["$$INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB["$BLC"]],
                       ["$$RESTART$$",                        LanguageDB["$label-def"]("$input", skipper_index)],
                       ["$$RELOAD$$",                         LanguageDB["$label-def"]("$reload", skipper_index)],
                       ["$$DROP_OUT_DIRECT$$",                LanguageDB["$label-def"]("$drop-out-direct", skipper_index)],
                       ["$$SKIPPER_INDEX$$",                  repr(skipper_index)],
                       ["$$GOTO_TERMINAL_EOF$$",              LanguageDB["$goto"]("$terminal-EOF")],
                       # When things were skipped, no change to acceptance flags or modes has
                       # happend. One can jump immediately to the start without re-entry preparation.
                       ["$$GOTO_START$$",                     LanguageDB["$goto"]("$start")], 
                       ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                       ["$$ON_TRIGGER_SET_TO_LOOP_START$$",   iteration_code],
                      ])

    code_str = txt
    ## code_str = blue_print(txt,
    ##                          [["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", skipper_index)]])

    local_variable_db = { "QUEX_OPTION_COLUMN_NUMBER_COUNTING/reference_p" : 
                          [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", None] }

    return code_str, local_variable_db

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

    end_procedure = "        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                    "                                    - reference_p));\n" 
    before_reload  = "       __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                     "                                   - reference_p));\n" 
    after_reload   = "           __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n" 

    return blue_print(code_str,
                     [["$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$", variable_definition],
                      ["$$LC_COUNT_IN_LOOP$$",                     in_loop],
                      ["$$LC_COUNT_END_PROCEDURE$$",               end_procedure],
                      ["$$LC_COUNT_BEFORE_RELOAD$$",               before_reload],
                      ["$$LC_COUNT_AFTER_RELOAD$$",                after_reload],
                      ])
