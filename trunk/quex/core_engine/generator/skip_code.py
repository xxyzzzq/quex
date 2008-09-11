import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core_engine.state_machine.index as sm_index
import quex.core_engine.utf8 as utf8
from   quex.frs_py.string_handling import blue_print
from   quex.core_engine.generator.drop_out import __reload_forward

range_skipper_template = """
    const QUEX_CHARACTER_TYPE   $$SKIPPER$$_Delimiter = { $$DELIMITER$$ };
    QUEX_CHARACTER_TYPE*        content_end = QuexBuffer_content_end(&me->buffer);

$$SKIPPER$$:
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) 
        goto $$SKIPPER$$_DROP_OUT;

$$SKIPPER$$_RESTART:
    *content_end = $$SKIPPER$$_Delimiter[0];       /* Overwrite BufferLimitCode (BLC).  */
    while( *QuexBuffer_input_get(&me->buffer) != $$SKIPPER$$_Delimiter[0] )
        QuexBuffer_input_p_increment(&me->buffer); /* Now, BLC cannot occur. See above. */
    *content_end = QUEX_SETTING_BUFFER_LIMIT_CODE; /* Reset BLC.                        */

    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ - 1 ) $$SKIPPER$$_DROP_OUT;

    /* BLC will cause a mismatch, and drop out after RESTART                            */
$$DELIMITER_REMAINDER_TEST$$            
    goto REENTRY_PREPARATION; /* End of range reached. */
 
$$SKIPPER$$_DROP_OUT:
    /* When loading new content it is always taken care that the beginning of the lexeme
     * is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     * the lexeme at all, so do not restrict the load procedure and set the lexeme start
     * to the actual input position.                                                    */
    QuexBuffer_mark_lexeme_start(&me->buffer); 
    $$RELOAD$$;
    if( QuexBuffer_distance_input_to_end_of_content(&me->buffer) < $$DELIMITER_LENGTH$$ ) {
       $$MISSING_CLOSING_DELIMITER$$
    }
    content_end = QuexBuffer_content_end(&me->buffer);
    $$SKIPPER$$_RESTART;
"""

def get_range_skipper(EndSequence, LanguageDB, MissingClosingDelimiterAction=""):
    """Produces a 'range skipper' until an ending string occurs. This follows 
       the following scheme:
    """
    assert EndSequence.__class__  == list
    assert len(EndSequence) >= 1
    assert map(type, EndSequence) == [int] * len(EndSequence)

    # Name the $$SKIPPER$$
    index = sm_index.get()
    skipper_str = LanguageDB["$label"](index)

    # Determine the $$DELIMITER$$
    delimiter_str = ""
    for letter in EndSequence:
        delimiter_str += "0x%X /* %s */, " % (letter, utf8.map_unicode_to_utf8(letter))
    delimiter_length_str = "%i" % len(EndSequence)


    if len(EndSequence) == 1: 
        delimiter_remainder_test_str = "    /* Oll Korrekt, delimiter has only length '1' */"
    else:
        txt = ""
        i = 0
        for letter in EndSequence[1:]:
            i += 1
            txt += "    QuexBuffer_input_p_increment(&me->buffer);\n"
            txt += "    if( QuexBuffer_input_get(&me->buffer) != $$SKIPPER$$_Delimiter[%i] )\n" %i
            txt += "        goto $$SKIPPER$$_RESTART;\n" 
        delimiter_remainder_test_str = txt

    code_str = blue_print(range_skipper_template,
                          [["$$DELIMITER$$",                 delimiter_str],
                           ["$$DELIMITER_LENGTH$$",          delimiter_length_str],
                           ["$$RELOAD$$",                    __reload_forward(index, )],
                           ["$$DELIMITER_REMAINDER_TEST$$",  delimiter_remainder_test_str],
                           ["$$MISSING_CLOSING_DELIMITER$$", MissingClosingDelimiterAction]])
    # Replace 'skipper_str' only after everything has been expanded
    return code_str.replace("$$SKIPPER$$", skipper_str)


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


