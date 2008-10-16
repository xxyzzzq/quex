import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.input.setup import setup as Setup
import quex.core_engine.state_machine.index as sm_index
import quex.core_engine.utf8 as utf8
from   quex.frs_py.string_handling               import blue_print
from   quex.core_engine.generator.drop_out       import get_forward_load_procedure
from   quex.core_engine.generator.languages.core import __nice
import quex.core_engine.generator.transition_block as transition_block
from   quex.core_engine.state_machine.transition_map import TransitionMap 

def do(SkipperDescriptor, PostContextN):
    LanguageDB = Setup.language_db
    skipper_class = SkipperDescriptor.__class__.__name__
    assert skipper_class in ["RangeSkipper"]

    if skipper_class == "RangeSkipper":
        return  "{\n" \
                + LanguageDB["$comment"]("Range skipper state") \
                + get_range_skipper(SkipperDescriptor.get_closing_sequence(), LanguageDB, PostContextN) \
                + "\n}\n"
    else:
        assert None

range_skipper_template = """
    $$DELIMITER_COMMENT$$
    const QUEX_CHARACTER_TYPE   SkipDelimiter$$SKIPPER_INDEX$$[] = { $$DELIMITER$$ };
    const size_t                SkipDelimiter$$SKIPPER_INDEX$$L  = $$DELIMITER_LENGTH$$;
    QUEX_CHARACTER_TYPE*        content_end = QuexBuffer_text_end(&me->buffer);

$$ENTRY$$
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QuexBuffer_content_size(&me->buffer) >= SkipDelimiter$$SKIPPER_INDEX$$L );
    if( QuexBuffer_distance_input_to_text_end(&me->buffer) < SkipDelimiter$$SKIPPER_INDEX$$L ) 
        $$GOTO_DROP_OUT$$

$$RESTART$$
    *content_end = SkipDelimiter$$SKIPPER_INDEX$$[0];       /* Overwrite BufferLimitCode (BLC).  */
    $$WHILE_1_PLUS_1_EQUAL_2$$
        $$INPUT_GET$$ 
        $$IF_INPUT_EQUAL_DELIMITER_0$$
            $$BREAK$$
        $$ENDIF$$
        $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$END_WHILE$$
    *content_end = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC.                        */

    /* BLC will cause a mismatch, and drop out after RESTART                            */
$$DELIMITER_REMAINDER_TEST$$            
    {
        /* 'input_p' points to a delimiter character which cannot be the buffer limit code.
         * Thus, we are not standing on '_end_of_file_p' or '_memory._back'. Thus, we can
         * increment the 'input_p' without exceeding the borders.                       */
        $$INPUT_P_INCREMENT$$ 
        /* NOTE: The initial state does not increment the input_p. When it detects that
         * it is located on a buffer border, it automatically triggers a reload. No 
         * need here to reload the buffer. */
        $$GOTO_REENTRY_PREPARATION$$ /* End of range reached. */
    }
$$DROP_OUT$$
    /* -- When loading new content it is always taken care that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                    */
    /* -- HOWEVER: See above, the reload procedure may be called while the input_p is not 
     *    pointing to the buffer border. Trick: 
     *    (1) We set the lexeme start to the current input_p. 
     *        The lexeme start is subject to appropriate pointer adaptions while loading. 
     *        Thus, the 'real' position of the input_p remains available via lexeme start pointer.
     *    (2) The input_p is set to a buffer border (so that all pre-conditions for load are met).
     *    (3) Load
     *    (4) Set the input_p to the lexeme start pointer.                                 */
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    $$MARK_LEXEME_START$$
    me->buffer._input_p = content_end;
    if( QuexAnalyser_buffer_reload_forward(&me->buffer, &last_acceptance_input_position,
                                           post_context_start_position, $$POST_CONTEXT_N$$) ) {

        me->buffer._input_p = me->buffer._lexeme_start_p;
        if( QuexBuffer_distance_input_to_text_end(&me->buffer) >= SkipDelimiter$$SKIPPER_INDEX$$L ) {
            content_end = QuexBuffer_text_end(&me->buffer);
            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$GOTO_RESTART$$
        }

    }
    me->buffer._input_p = me->buffer._lexeme_start_p;
    $$MISSING_CLOSING_DELIMITER$$
"""

def get_range_skipper(EndSequence, LanguageDB, PostContextN, MissingClosingDelimiterAction=""):
    assert EndSequence.__class__  == list
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

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
    if len(EndSequence) == 1: 
        txt  = "    if( QuexBuffer_distance_input_to_text_end(&me->buffer) == 0  )\n"
        txt += "        $$GOTO_DROP_OUT$$\n"
        txt += "    " + LanguageDB["$comment"]("No further check. Delimiter has length '1'")
        delimiter_remainder_test_str = txt
    else:
        txt  = "    if( QuexBuffer_distance_input_to_text_end(&me->buffer) < SkipDelimiter$$SKIPPER_INDEX$$L )\n"
        txt += "        $$GOTO_DROP_OUT$$\n"
        i = 0
        for letter in EndSequence[1:]:
            i += 1
            txt += "    " + LanguageDB["$input/increment"] + "\n"
            txt += "    " + LanguageDB["$input/get"] + "\n"
            txt += "    " + LanguageDB["$if !="]("SkipDelimiter$$SKIPPER_INDEX$$[%i]" % i)
            txt += "         " + LanguageDB["$goto"]("$input", skipper_index) + "\n"
            txt += "    " + LanguageDB["$endif"]
        delimiter_remainder_test_str = txt

    code_str = blue_print(range_skipper_template,
                          [["$$DELIMITER$$",                  delimiter_str],
                           ["$$DELIMITER_LENGTH$$",           delimiter_length_str],
                           ["$$DELIMITER_COMMENT$$",          delimiter_comment_str],
                           ["$$WHILE_1_PLUS_1_EQUAL_2$$",     LanguageDB["$loop-start-endless"]],
                           ["$$END_WHILE$$",                  LanguageDB["$loop-end"]],
                           ["$$INPUT_P_INCREMENT$$",          LanguageDB["$input/increment"]],
                           ["$$INPUT_GET$$",                  LanguageDB["$input/get"]],
                           ["$$IF_INPUT_EQUAL_DELIMITER_0$$", LanguageDB["$if =="]("SkipDelimiter$$SKIPPER_INDEX$$[0]")],
                           ["$$BREAK$$",                      LanguageDB["$break"]],
                           ["$$ENDIF$$",                      LanguageDB["$endif"]],
                           ["$$ENTRY$$",                      LanguageDB["$label-def"]("$entry", skipper_index)],
                           ["$$RESTART$$",                    LanguageDB["$label-def"]("$input", skipper_index)],
                           ["$$DROP_OUT$$",                   LanguageDB["$label-def"]("$drop-out", skipper_index)],
                           ["$$GOTO_RESTART$$",               LanguageDB["$goto"]("$input", skipper_index)],
                           ["$$GOTO_REENTRY_PREPARATION$$",   LanguageDB["$goto"]("$re-start")],
                           ["$$MARK_LEXEME_START$$",          LanguageDB["$mark-lexeme-start"]],
                           ["$$POST_CONTEXT_N$$",             repr(PostContextN)],
                           ["$$DELIMITER_REMAINDER_TEST$$",   delimiter_remainder_test_str],
                           ["$$MISSING_CLOSING_DELIMITER$$",  MissingClosingDelimiterAction]])

    code_str = blue_print(code_str,
                          [["$$SKIPPER_INDEX$$", __nice(skipper_index)],
                           ["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", skipper_index)]])

    return code_str


skipper_template = """
{ 
    $$DELIMITER_COMMENT$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QuexBuffer_content_size(&me->buffer) >= 1);
    if( QuexBuffer_distance_input_to_text_end(&me->buffer) != 0 ) 
        $$GOTO_DROP_OUT$$

    /* NOTE: For simple skippers the end of content does not have to be overwriten 
     *       with anything (as done for range skippers). This is so, because the abort
     *       criteria is that a character occurs which does not belong to the trigger 
     *       set. The BufferLimitCode, though, does never belong to any trigger set and
     *       thus, no special character is to be set.                                   */
$$LOOP_START$$
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$INPUT_GET$$ 
$$ON_TRIGGER_SET_TO_LOOP_START$$

$$DROP_OUT$$
    /* -- When loading new content it is always taken care that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                   
     * -- The input_p will at this point in time always point to the buffer border.        */
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    $$MARK_LEXEME_START$$
    if( QuexAnalyser_buffer_reload_forward(&me->buffer, &last_acceptance_input_position,
                                           post_context_start_position, $$POST_CONTEXT_N$$) ) {

        if( QuexBuffer_distance_input_to_text_end(&me->buffer) != 0 ) {
            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$GOTO_LOOP_START$$
        }

    }
    $$MISSING_CLOSING_DELIMITER$$

$$DROP_OUT_DIRECT$$
    /* There was no buffer limit code, so no end of buffer or end of file --> continue analysis */
    $$GOTO_REENTRY_PREPARATION$$                           
}
"""

def get_character_set_skipper(TriggerSet, LanguageDB, PostContextN, MissingClosingDelimiterAction):
    """This function implements simple 'skipping' in the sense of passing by
       characters that belong to a given set of characters--the TriggerSet.
    """
    assert TriggerSet.__class__.__name__ == "NumberSet"
    assert not TriggerSet.is_empty()

    skipper_index = sm_index.get()
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.
    transition_map = TransitionMap()
    transition_map.add_transition(TriggerSet, skipper_index)
    iteration_code = transition_block.do(transition_map.get_trigger_map(), skipper_index, InitStateF=False, DSM=None)

    comment_str = LanguageDB["$comment"]("Skip any character in " + TriggerSet.get_utf8_string())

    txt = blue_print(skipper_template,
                      [
                       ["$$DELIMITER_COMMENT$$",          comment_str],
                       ["$$INPUT_P_INCREMENT$$",          LanguageDB["$input/increment"]],
                       ["$$INPUT_GET$$",                  LanguageDB["$input/get"]],
                       ["$$IF_INPUT_EQUAL_DELIMITER_0$$", LanguageDB["$if =="]("SkipDelimiter$$SKIPPER_INDEX$$[0]")],
                       ["$$ENDIF$$",                      LanguageDB["$endif"]],
                       ["$$LOOP_START$$",                 LanguageDB["$label-def"]("$entry", skipper_index)],
                       ["$$RESTART$$",                    LanguageDB["$label-def"]("$input", skipper_index)],
                       ["$$DROP_OUT$$",                   LanguageDB["$label-def"]("$drop-out", skipper_index)],
                       ["$$DROP_OUT_DIRECT$$",            LanguageDB["$label-def"]("$drop-out-direct", skipper_index)],
                       ["$$GOTO_LOOP_START$$",            LanguageDB["$goto"]("$entry", skipper_index)],
                       ["$$GOTO_REENTRY_PREPARATION$$",   LanguageDB["$goto"]("$re-start")],
                       ["$$MARK_LEXEME_START$$",          LanguageDB["$mark-lexeme-start"]],
                       ["$$POST_CONTEXT_N$$",             repr(PostContextN)],
                       ["$$ON_TRIGGER_SET_TO_LOOP_START$$", iteration_code],
                       ["$$MISSING_CLOSING_DELIMITER$$",    MissingClosingDelimiterAction],
                      ])

    return blue_print(txt,
                       [["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", skipper_index)]])

def get_nested_character_skipper(StartSequence, EndSequence, LanguageDB, BufferEndLimitCode,
                                 BufferReloadRequiredOnDropOutF=True):
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


