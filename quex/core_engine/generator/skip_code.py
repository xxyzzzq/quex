import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.state_machine.index as sm_index
import quex.core_engine.utf8 as utf8
from   quex.frs_py.string_handling import blue_print
from   quex.core_engine.generator.drop_out import __reload_forward
from   quex.core_engine.generator.languages.core import label_db

range_skipper_template = """
    const QUEX_CHARACTER_TYPE   SkipDelimiter$$SKIPPER_INDEX$$ = { $$DELIMITER$$ };
    QUEX_CHARACTER_TYPE*        content_end = QuexBuffer_content_end(&me->buffer);

$$SKIPPER_ENTRY$$
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) 
        goto $$SKIPPER$$_DROP_OUT;

$$SKIPPER_RESTART$$
    *content_end = $$SKIPPER$$_Delimiter[0];       /* Overwrite BufferLimitCode (BLC).  */
    while( *QuexBuffer_input_get(&me->buffer) != SkipDelimiter$$SKIPPER_INDEX$$[0] )
        QuexBuffer_input_p_increment(&me->buffer); /* Now, BLC cannot occur. See above. */
    *content_end = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC.                        */

    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ - 1 ) 
        $$GOTO_SKIPPER_DROP_OUT$$

    /* BLC will cause a mismatch, and drop out after RESTART                            */
$$DELIMITER_REMAINDER_TEST$$            
    $$GOTO_REENTRY_PREPARATION$$ /* End of range reached. */
 
$$SKIPPER_DROP_OUT$$
    /* When loading new content it is always taken care that the beginning of the lexeme
     * is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     * the lexeme at all, so do not restrict the load procedure and set the lexeme start
     * to the actual input position.                                                    */
    QuexBuffer_mark_lexeme_start(&me->buffer); 
    $$RELOAD$$
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) {
       $$MISSING_CLOSING_DELIMITER$$
    }
    content_end = QuexBuffer_content_end(&me->buffer);
    $$GOTO_SKIPPER_RESTART$$
"""

def get_load_procedure(SM):
    arg_list = ""
    for state_machine_id in SM.post_contexted_sm_id_list():
        arg_list += ", &last_acceptance_%s_input_position" % state_machine_id
    txt  = '    QUEX_DEBUG_PRINT(&me->buffer, "FORWARD_BUFFER_RELOAD");\n'
    txt += "    if( $$QUEX_ANALYZER_STRUCT_NAME$$_%s_buffer_reload_forward(&me->buffer, &last_acceptance_input_position%s) ) {\n" % \
            (SM.name(), arg_list)
    txt += "       " + LanguageDB["$goto"]("$skipper", StateIndex) + "\n"
    txt += "    " + LanguageDB["$endif"]                           + "\n"

def get_range_skipper(EndSequence, LanguageDB, MissingClosingDelimiterAction=""):
    """Produces a 'range skipper' until an ending string occurs. This follows 
       the following scheme:
    """
    assert EndSequence.__class__  == list
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

    # Name the $$SKIPPER$$
    skipper_index = sm_index.get()

    # Determine the $$DELIMITER$$
    delimiter_str = ""
    delimiter_comment_str = ""
    for letter in EndSequence:
        delimiter_comment_str += "'%s', " % utf8.map_unicode_to_utf8(letter)
        delimiter_str += "0x%X, " % (letter, 
    delimiter_length_str = "%i" % len(EndSequence)

    if len(EndSequence) == 1: 
        delimiter_remainder_test_str = "    " + LanguageDB["$comment"]("Oll Korrekt, delimiter has only length '1'")
    else:
        txt = ""
        i = 0
        for letter in EndSequence[1:]:
            i += 1
            txt += "    " + LanguageDB["$increment"]
            txt += "    if( QuexBuffer_input_get(&me->buffer) != SkipDelimiter$$SKIPPER_INDEX$$[%i] )\n" %i
            txt += "         " + LanguageDB[$goto]("$skipper-restart", skipper_index)
        delimiter_remainder_test_str = txt

    code_str = blue_print(range_skipper_template,
                          [["$$DELIMITER$$",                 delimiter_str],
                           ["$$DELIMITER_LENGTH$$",          delimiter_length_str],
                           ["$$RELOAD$$",                    __reload_forward(index, )],
                           ["$$DELIMITER_REMAINDER_TEST$$",  delimiter_remainder_test_str],
                           ["$$MISSING_CLOSING_DELIMITER$$", MissingClosingDelimiterAction]])


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


