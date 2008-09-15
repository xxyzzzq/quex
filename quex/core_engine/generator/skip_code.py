import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.state_machine.index as sm_index
import quex.core_engine.utf8 as utf8
from   quex.frs_py.string_handling               import blue_print
from   quex.core_engine.generator.drop_out       import get_forward_load_procedure
from   quex.core_engine.generator.languages.core import __nice

range_skipper_template = """
    $$DELIMITER_COMMENT$$
    const QUEX_CHARACTER_TYPE   SkipDelimiter$$SKIPPER_INDEX$$[] = { $$DELIMITER$$ };
    QUEX_CHARACTER_TYPE*        content_end = QuexBuffer_text_end(&me->buffer);

$$SKIPPER_ENTRY$$
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) 
        $$GOTO_SKIPPER_DROP_OUT$$;

$$SKIPPER_RESTART$$
    *content_end = SkipDelimiter$$SKIPPER_INDEX$$[0];       /* Overwrite BufferLimitCode (BLC).  */
    while( QuexBuffer_input_get(&me->buffer) != SkipDelimiter$$SKIPPER_INDEX$$[0] )
        QuexBuffer_input_p_increment(&me->buffer); /* Now, BLC cannot occur. See above. */
    *content_end = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC.                        */

    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ - 1 ) 
        $$GOTO_SKIPPER_DROP_OUT$$

    /* BLC will cause a mismatch, and drop out after RESTART                            */
$$DELIMITER_REMAINDER_TEST$$            
    $$GOTO_REENTRY_PREPARATION$$ /* End of range reached. */
 
$$SKIPPER_DROP_OUT$$
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
    $$MARK_LEXEME_START$$
    me->buffer._input_p = content_end;
$$RELOAD$$
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) {
       $$MISSING_CLOSING_DELIMITER$$
    }
    me->buffer._input_p = me->buffer._lexeme_start_p;
    content_end = QuexBuffer_text_end(&me->buffer);
    $$GOTO_SKIPPER_RESTART$$
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
        delimiter_remainder_test_str = "    " + LanguageDB["$comment"]("Oll Korrekt, delimiter has only length '1'")
    else:
        txt = ""
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
                          [["$$DELIMITER$$",                 delimiter_str],
                           ["$$DELIMITER_LENGTH$$",          delimiter_length_str],
                           ["$$DELIMITER_COMMENT$$",         delimiter_comment_str],
                           ["$$SKIPPER_ENTRY$$",             LanguageDB["$label-def"]("$entry", skipper_index)],
                           ["$$SKIPPER_RESTART$$",           LanguageDB["$label-def"]("$input", skipper_index)],
                           ["$$SKIPPER_DROP_OUT$$",          LanguageDB["$label-def"]("$drop-out", skipper_index)],
                           ["$$GOTO_SKIPPER_DROP_OUT$$",     LanguageDB["$goto"]("$drop-out", skipper_index)],
                           ["$$GOTO_SKIPPER_RESTART$$",      LanguageDB["$goto"]("$input", skipper_index)],
                           ["$$GOTO_REENTRY_PREPARATION$$",  LanguageDB["$goto"]("$re-start")],
                           ["$$MARK_LEXEME_START$$",         LanguageDB["$mark-lexeme-start"]],
                           ["$$RELOAD$$",                    get_forward_load_procedure(skipper_index, PostContextN)],
                           ["$$DELIMITER_REMAINDER_TEST$$",  delimiter_remainder_test_str],
                           ["$$MISSING_CLOSING_DELIMITER$$", MissingClosingDelimiterAction]])

    code_str = code_str.replace("$$SKIPPER_INDEX$$", __nice(skipper_index))
            

    return code_str

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


