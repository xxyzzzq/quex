import os
import sys
from   copy import deepcopy
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.frs_py.string_handling                   import blue_print
from   quex.input.setup                              import setup as Setup
import quex.core_engine.utf8                         as     utf8
import quex.core_engine.state_machine.index          as     sm_index
from   quex.core_engine.state_machine.transition_map import TransitionMap 
from   quex.core_engine.generator.languages.core     import __nice
import quex.core_engine.generator.state_coder.transition_block as transition_block

def do(SkipperDescriptor):
    """RETURNS: code_str --  a string containing source code of the skipper
                db       --  database on required local variables
    """
    LanguageDB = Setup.language_db
    skipper_class = SkipperDescriptor.__class__.__name__
    assert skipper_class in ["SkipperRange", "SkipperCharacterSet"]

    if skipper_class == "SkipperRange":
        return  create_skip_range_code(SkipperDescriptor.get_closing_sequence())
    elif skipper_class == "SkipperCharacterSet":
        return  create_skip_character_set_code(SkipperDescriptor.get_character_set())
    else:
        assert None, None

def create_skip_range_code(ClosingSequence):
    LanguageDB   = Setup.language_db

    code_str, db = get_range_skipper(ClosingSequence) 

    txt =    "{\n"                                          \
           + LanguageDB["$comment"]("Range skipper state")  \
           + code_str                                       \
           + "\n}\n"

    return code_str, db

def create_skip_character_set_code(CharacterSet):
    LanguageDB   = Setup.language_db

    code_str, db = get_character_set_skipper(CharacterSet)   

    txt =   "{\n"                                                 \
          + LanguageDB["$comment"]("Character set skipper state") \
          + code_str                                              \
          + "\n}\n"

    return txt, db

range_skipper_template = """
{
    $$DELIMITER_COMMENT$$
    const QUEX_TYPE_CHARACTER   Skipper$$SKIPPER_INDEX$$[] = { $$DELIMITER$$ };
    const size_t                Skipper$$SKIPPER_INDEX$$L  = $$DELIMITER_LENGTH$$;
    QUEX_TYPE_CHARACTER*        text_end = QUEX_NAME(Buffer_text_end)(&me->buffer);
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

$$ENTRY$$
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= Skipper$$SKIPPER_INDEX$$L );

    /* NOTE: If _input_p == end of buffer, then it will drop out immediately out of the
     *       loop below and drop into the buffer reload procedure.                      */

    /* Loop eating characters: Break-out as soon as the First Character of the Delimiter
     * (FCD) is reached. Thus, the FCD plays also the role of the Buffer Limit Code. There
     * are two reasons for break-out:
     *    (1) we reached a limit (end-of-file or buffer-limit)
     *    (2) there was really the FCD in the character stream
     * This must be distinguished after the loop was exited. But, during the 'swallowing' we
     * are very fast, because we do not have to check for two different characters.        */
    *text_end = Skipper$$SKIPPER_INDEX$$[0]; /* Overwrite BufferLimitCode (BLC).  */
    $$WHILE_1_PLUS_1_EQUAL_2$$
        $$INPUT_GET$$ 
        $$IF_INPUT_EQUAL_DELIMITER_0$$
            $$LC_COUNT_LOOP_EXIT$$
        $$ENDIF$$
$$LC_COUNT_IN_LOOP$$
        $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$END_WHILE$$
    *text_end = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC. */

    /* Case (1) and (2) from above can be distinguished easily: 
     *
     *   (1) Distance to text end == 0: 
     *         End-of-File or Buffer-Limit. 
     *         => goto to drop-out handling
     *
     *   (2) Else:                      
     *         First character of delimit reached. 
     *         => For the verification of the tail of the delimiter it is 
     *            essential that it is loaded completely into the buffer. 
     *            For this, it must be required:
     *
     *                Distance to text end >= Delimiter length 
     *
     *                _input_p    end
     *                    |        |           end - _input_p >= 3
     *                [ ][R][E][M][#]          
     * 
     *         The case of reload should be seldom and is costy anyway. 
     *         Thus let's say, that in this case we simply enter the drop 
     *         out and start the search for the delimiter all over again.
     *
     *         (2.1) Distance to text end < Delimiter length
     *                => goto to drop-out handling
     *         (2.2) Start detection of tail of delimiter
     *
     */
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        /* (1) */
        $$GOTO_DROP_OUT$$            
    } 
    else if( QUEX_NAME(Buffer_distance_input_to_text_end)(&me->buffer) < Skipper$$SKIPPER_INDEX$$L ) {
        /* (2.1) */
        $$GOTO_DROP_OUT$$            
    }
    /* (2.2) Test the remaining delimiter, but note, that the check must restart at '_input_p + 1'
     *       if any later check fails.                                                              */
    $$INPUT_P_INCREMENT$$
    /* Example: Delimiter = '*', '/'; if we get ...[*][*][/]... then the the first "*" causes 
     *          a drop out out of the 'swallowing loop' and the second "*" will mismatch 
     *          the required "/". But, then the second "*" must be presented to the
     *          swallowing loop and the letter after it completes the 'match'.
     * (The whole discussion, of course, is superflous if the range delimiter has length 1.)  */
$$DELIMITER_REMAINDER_TEST$$            
    {
        $$SET_INPUT_P_BEHIND_DELIMITER$$ 
        /* NOTE: The initial state does not increment the input_p. When it detects that
         * it is located on a buffer border, it automatically triggers a reload. No 
         * need here to reload the buffer. */
$$LC_COUNT_END_PROCEDURE$$
        /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
        $$GOTO_START$$ /* End of range reached. */
    }

$$DROP_OUT$$
    QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(&me->buffer);
    /* -- When loading new content it is checked that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                    */
    /* -- According to case (2.1) is is possible that the _input_p does not point to the end
     *    of the buffer, thus we record the current position in the lexeme start pointer and
     *    recover it after the loading. */
    $$MARK_LEXEME_START$$
    me->buffer._input_p = text_end;
$$LC_COUNT_BEFORE_RELOAD$$
    if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) == false ) {
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        /* Recover '_input_p' from lexeme start 
         * (inverse of what we just did before the loading) */
        me->buffer._input_p = me->buffer._lexeme_start_p;
        /* After reload, we need to increment _input_p. That's how the game is supposed to be played. 
         * But, we recovered from lexeme start pointer, and this one does not need to be incremented. */
        text_end = QUEX_NAME(Buffer_text_end)(&me->buffer);
$$LC_COUNT_AFTER_RELOAD$$
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        $$GOTO_ENTRY$$
    }
    /* Here, either the loading failed or it is not enough space to carry a closing delimiter */
    me->buffer._input_p = me->buffer._lexeme_start_p;
    $$MISSING_CLOSING_DELIMITER$$
}
"""

def get_range_skipper(EndSequence, MissingClosingDelimiterAction=""):
    assert EndSequence.__class__  == list
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

    LanguageDB   = Setup.language_db

    # Name the $$SKIPPER$$
    skipper_index = sm_index.get()

    # Determine the $$DELIMITER$$
    delimiter_str = ""
    delimiter_comment_str = "                         Delimiter: "
    for letter in EndSequence:
        delimiter_comment_str += "'%s', " % utf8.map_unicode_to_utf8(letter)
        delimiter_str += "0x%X, " % letter
    delimiter_length_str = "%i" % len(EndSequence)
    delimiter_comment_str = LanguageDB["$comment"](delimiter_comment_str) 

    # Determine the check for the tail of the delimiter
    delimiter_remainder_test_str = ""
    if len(EndSequence) != 1: 
        txt = ""
        i = 0
        for letter in EndSequence[1:]:
            i += 1
            txt += "    " + LanguageDB["$input/get-offset"](i-1) + "\n"
            txt += "    " + LanguageDB["$if !="]("Skipper$$SKIPPER_INDEX$$[%i]" % i)
            txt += "         " + LanguageDB["$goto"]("$entry", skipper_index) + "\n"
            txt += "    " + LanguageDB["$endif"]
        delimiter_remainder_test_str = txt

    # The main part
    code_str = blue_print(range_skipper_template,
                          [["$$DELIMITER$$",                      delimiter_str],
                           ["$$DELIMITER_LENGTH$$",               delimiter_length_str],
                           ["$$DELIMITER_COMMENT$$",              delimiter_comment_str],
                           ["$$WHILE_1_PLUS_1_EQUAL_2$$",         LanguageDB["$loop-start-endless"]],
                           ["$$END_WHILE$$",                      LanguageDB["$loop-end"]],
                           ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                           ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                           ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                           ["$$INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB["$BLC"]],
                           ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("Skipper$$SKIPPER_INDEX$$[0]")],
                           ["$$ENDIF$$",                          LanguageDB["$endif"]],
                           ["$$ENTRY$$",                          LanguageDB["$label-def"]("$entry", skipper_index)],
                           ["$$DROP_OUT$$",                       LanguageDB["$label-def"]("$drop-out", skipper_index)],
                           ["$$GOTO_ENTRY$$",                     LanguageDB["$goto"]("$entry", skipper_index)],
                           # When things were skipped, no change to acceptance flags or modes has
                           # happend. One can jump immediately to the start without re-entry preparation.
                           ["$$GOTO_START$$",                     LanguageDB["$goto"]("$start")], 
                           ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                           ["$$DELIMITER_REMAINDER_TEST$$",       delimiter_remainder_test_str],
                           ["$$SET_INPUT_P_BEHIND_DELIMITER$$",   LanguageDB["$input/add"](len(EndSequence)-1)],
                           ["$$MISSING_CLOSING_DELIMITER$$",      MissingClosingDelimiterAction],
                          ])

    # Line and column number counting
    code_str, reference_p_f = __range_skipper_lc_counting_replacements(code_str, EndSequence)

    # The finishing touch
    code_str = blue_print(code_str,
                          [["$$SKIPPER_INDEX$$", __nice(skipper_index)],
                           ["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", skipper_index)]])

    if reference_p_f:
        local_variable_db = { "reference_p" : 
                              [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", None, "CountColumns"] }
    else:
        local_variable_db = {}

    return code_str, local_variable_db


trigger_set_skipper_template = """
{ 
    $$DELIMITER_COMMENT$$
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);
#if 0
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        $$GOTO_DROP_OUT$$
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
$$LOOP_REENTRANCE$$
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$GOTO_LOOP_START$$

$$DROP_OUT$$
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

$$DROP_OUT_DIRECT$$
$$LC_COUNT_END_PROCEDURE$$
    /* There was no buffer limit code, so no end of buffer or end of file --> continue analysis 
     * The character we just swallowed must be re-considered by the main state machine.
     * But, note that the initial state does not increment '_input_p'!
     */
    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
    $$GOTO_START$$                           
}
"""

def get_character_set_skipper(TriggerSet):
    """This function implements simple 'skipping' in the sense of passing by
       characters that belong to a given set of characters--the TriggerSet.
    """
    assert TriggerSet.__class__.__name__ == "NumberSet"
    assert not TriggerSet.is_empty()

    LanguageDB = Setup.language_db

    skipper_index = sm_index.get()
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.
    transition_map = TransitionMap() # (don't worry about 'drop-out-ranges' etc.)
    transition_map.add_transition(TriggerSet, skipper_index)
    iteration_code = "".join(transition_block.do(transition_map.get_trigger_map(), skipper_index, DSM=None))

    comment_str = LanguageDB["$comment"]("Skip any character in " + TriggerSet.get_utf8_string())

    # Line and column number counting
    code_str = __set_skipper_lc_counting_replacements(trigger_set_skipper_template, TriggerSet)

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
                       ["$$DROP_OUT$$",                       LanguageDB["$label-def"]("$drop-out", skipper_index)],
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
    # code_str = blue_print(txt,
    #                          [["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", skipper_index)]])

    local_variable_db = { "reference_p" : 
                          [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", None, "CountColumns"] }

    return code_str, local_variable_db

def get_nested_character_skipper(StartSequence, EndSequence, LanguageDB, BufferEndLimitCode):
    assert StartSequence.__class__  == list
    assert len(StartSequence)       >= 1
    assert map(type, StartSequence) == [int] * len(StartSequence)
    assert EndSequence.__class__  == list
    assert len(EndSequence)       >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)
    assert StartSequence != EndSequence

    # Identify the common start of 'StartSequence' and 'EndSequence'
    CommonSequence    = []
    StartSequenceTail = []  # 'un-common' tail of the start sequence
    EndSequenceTail   = []  # 'un-common' tail of the end sequence
    L_min             = min(len(StartSequence), len(EndSequence))
    characters_from_begin_to_i_are_common_f = True
    for i in range(L_min):
        if (not characters_from_begin_to_i_are_common_f) or (StartSequence[i] != EndSequence[i]): 
            StartSequenceTail.append(StartSequence[i])
            EndSequenceTail.append(EndSequence[i])
            characters_from_begin_to_i_are_common_f = False
        else: 
            CommonSequence.append(StartSequence[i])

    if CommonSequence != []:
        msg += "        " + LanguageDB["$if =="](repr(CommonSequence[0]))
        msg += "            " + action_on_first_character_match
        msg += "        " + LanguageDB["$endif"]
    else:
        msg += "        " + LanguageDB["$if =="](repr(StartSequenceTail[0]))
        msg += "            " + action_on_first_character_match
        msg += "        " + LanguageDB["$endif"]


line_counter_in_loop = """
#       if defined(QUEX_OPTION_LINE_NUMBER_COUNTING)
        if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
            ++(me->counter._line_number_at_end);
        }
#       endif
"""

line_column_counter_in_loop = """
#       if defined(QUEX_OPTION_LINE_NUMBER_COUNTING) || defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)
        if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
            __QUEX_IF_COUNT_LINES(++(me->counter._line_number_at_end));
            __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));
            __QUEX_IF_COUNT_COLUMNS(me->counter._column_number_at_end = (size_t)0);
        }
#       endif
"""

def __range_skipper_lc_counting_replacements(code_str, EndSequence):
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
    LanguageDB = Setup.language_db

    def last_newline_index(Sequence):
        i = -1
        while 1 + 1 == 2:
            try:    i = Sequence.index(ord('\n'), i + 1)
            except: return i

    reference_p_def = ""

    in_loop         = ""
    end_procedure   = ""
    exit_loop       = ""
    before_reload   = ""
    after_reload    = ""
    exit_loop       = LanguageDB["$break"]

    reference_p_required_f = False

    # Line/Column Counting:
    newline_number_in_delimiter = EndSequence.count(ord('\n'))

    if EndSequence == map(ord, "\n") or EndSequence == map(ord, "\r\n"):
        #  (1) If the end-delimiter is a newline 
        #      => there cannot appear a newline inside the comment
        #      => IN LOOP: no line number increment
        #                  no reference pointer required for column counting
        column_n       = len(EndSequence) - (last_newline_index(EndSequence) + 1)
     
        end_procedure += "        __QUEX_IF_COUNT_COLUMNS_SET((size_t)%i);\n" % column_n 
        end_procedure += "        __QUEX_IF_COUNT_LINES_ADD((size_t)1);\n"

    else:
        #  (2) If end-delimiter is NOT newline
        #      => there can appear a newline inside the comment
        if newline_number_in_delimiter == 0:
            # -- no newlines in delimiter => line and column number 
            #                                must be counted.
            in_loop       = line_column_counter_in_loop
            end_procedure = "        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                            "                                    - reference_p));\n" 
            reference_p_required_f = True
        else:
            # -- newline inside delimiter => line number must be counted
            #                                column number is fixed.
            if    EndSequence[0] == ord('\n') \
               or len(EndSequence) > 1 and EndSequence[0:2] == [ord('\r'), ord('\n')]: 
                # If the first character in the sequence is newline, then the line counting
                # may is prevented by the loop exit. Now, we need to count.
               exit_loop = "__QUEX_IF_COUNT_LINES_ADD((size_t)1);\n" \
                           + exit_loop
            in_loop = line_counter_in_loop
            column_n       = len(EndSequence) - (last_newline_index(EndSequence) + 1)
            end_procedure += "        __QUEX_IF_COUNT_COLUMNS_SET((size_t)%i);\n" % column_n 
            end_procedure += "        __QUEX_IF_COUNT_LINES_ADD((size_t)%i);\n"   % newline_number_in_delimiter

        
    if reference_p_required_f:
        reference_p_def = "    __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"
        before_reload   = "    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                          "                                - reference_p));\n" 
        after_reload    = "        __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"

    return blue_print(code_str,
                     [["$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$", reference_p_def],
                      ["$$LC_COUNT_IN_LOOP$$",                     in_loop],
                      ["$$LC_COUNT_END_PROCEDURE$$",               end_procedure],
                      ["$$LC_COUNT_BEFORE_RELOAD$$",               before_reload],
                      ["$$LC_COUNT_AFTER_RELOAD$$",                after_reload],
                      ["$$LC_COUNT_LOOP_EXIT$$",                exit_loop],
                      ]), \
           reference_p_required_f


def __set_skipper_lc_counting_replacements(code_str, CharacterSet):
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
