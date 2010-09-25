from   quex.core_engine.generator.skipper.common import *
import quex.core_engine.state_machine.index      as     sm_index
from   quex.input.setup                          import setup as Setup
from   quex.frs_py.string_handling               import blue_print

def do(SkipperDescriptor):
    assert type(ArgumentList) == list
    assert len(ArgumentList) == 2
    assert type(ArgumentList[1]) in [str, unicode]

    LanguageDB      = Setup.language_db
    OpeningSequence = ArgumentList[0]
    ClosingSequence = ArgumentList[1]
    ModeName        = ArgumentList[2]

    Mode = None
    if ModeName != "":
        Mode = lexer_mode.mode_db[ModeName]

    code_str, db = get_skipper(OpeningSequence, ClosingSequence, Mode) 


    txt =    "{\n"                                          \
           + LanguageDB["$comment"]("Range skipper state")  \
           + code_str                                       \
           + "\n}\n"

    return code_str, db

template_str = """
{
    const QUEX_TYPE_CHARACTER   Opener$$SKIPPER_INDEX$$[]  = { $$OPENER$$ }; $$OPENER_COMMENT$$ 
    const QUEX_TYPE_CHARACTER*  Opener$$SKIPPER_INDEX$$End = Opener + $$OPENER_LENGTH$$;
    const QUEX_TYPE_CHARACTER*  Opener$$SKIPPER_INDEX$$_it = Opener;
    const QUEX_TYPE_CHARACTER   Closer$$SKIPPER_INDEX$$[]  = { $$CLOSER$$ }; $$OPENER_COMMENT$$ 
    const QUEX_TYPE_CHARACTER*  Closer$$SKIPPER_INDEX$$End = Closer + $$CLOSER_LENGTH$$;
    const QUEX_TYPE_CHARACTER*  Closer$$SKIPPER_INDEX$$_it = Closer;

    QUEX_TYPE_CHARACTER*        text_end = QUEX_NAME(Buffer_text_end)(&me->buffer);
$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$

$$ENTRY$$
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= $$OPENER_LENGTH$$ );

    /* NOTE: If _input_p == end of buffer, then it will drop out immediately out of the
     *       loop below and drop into the buffer reload procedure.                      */

    /* Loop eating characters: Break-out as soon as the First Character of the Delimiter
     * (FCD) is reached. Thus, the FCD plays also the role of the Buffer Limit Code. There
     * are two reasons for break-out:
     *    (1) we reached a limit (end-of-file or buffer-limit)
     *    (2) there was really the FCD in the character stream
     * This must be distinguished after the loop was exited. But, during the 'swallowing' 
     * we are very fast, because we do not have to check for two different characters.  */
    while( 1 + 1 == 2 ) {
        $$INPUT_GET$$ 
        if( input == *Opener$$SKIPPER_INDEX$$_it ) {
            ++Opener$$SKIPPER_INDEX$$_it;
            if( Opener$$SKIPPER_INDEX$$_it == Opener$$SKIPPER_INDEX$$End ) {
                --counter;
                if( counter == 0 ) {
                    /* NOTE: The initial state does not increment the input_p. When it detects that
                     * it is located on a buffer border, it automatically triggers a reload. No 
                     * need here to reload the buffer. */
                    $$LC_COUNT_END_PROCEDURE$$
                    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
                    $$GOTO_START$$ /* End of range reached. */
                }
                Opener$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Opener$$SKIPPER_INDEX$$;
            }
        }
        if( input == *Closer$$SKIPPER_INDEX$$_it ) {
            ++Closer$$SKIPPER_INDEX$$_it;
            if( Closer$$SKIPPER_INDEX$$_it == Closer$$SKIPPER_INDEX$$End ) {
                ++counter;
                Closer$$SKIPPER_INDEX$$_it = (QUEX_TYPE_CHARACTER*)Closer$$SKIPPER_INDEX$$;
            }
        }
        if( input == QUEX_SETTING_BUFFER_LIMIT_CODE ) {
            $$GOTO_DROP_OUT$$
        }
$$LC_COUNT_IN_LOOP$$
        $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
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
    $$ON_SKIP_RANGE_OPEN$$
}
}
"""

def get_skipper(OpenerSequence, CloserSequence, Mode):
    assert OpenerSequence.__class__  == list
    assert len(OpenerSequence)       >= 1
    assert map(type, OpenerSequence) == [int] * len(OpenerSequence)
    assert CloserSequence.__class__  == list
    assert len(CloserSequence)       >= 1
    assert map(type, CloserSequence) == [int] * len(CloserSequence)
    assert OpenerSequence != CloserSequence

    LanguageDB    = Setup.language_db

    skipper_index = sm_index.get()

    closer_str, closer_length_str, closer_comment_str = get_character_sequence(OpenerSequence)
    closer_str, closer_length_str, closer_comment_str = get_character_sequence(CloserSequence)

    local_variable_db = { 
        "counter":     [ "size_t", "0", None],
        "reference_p": [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", 
                         None, "CountColumns"], 
    }

    code_str = blue_print(template_str,
                          [["$$DELIMITER$$",                      delimiter_str],
                           ["$$DELIMITER_LENGTH$$",               delimiter_length_str],
                           ["$$DELIMITER_COMMENT$$",              delimiter_comment_str],
                           ["$$WHILE_1_PLUS_1_EQUAL_2$$",         LanguageDB["$loop-start-endless"]],
                           ["$$END_WHILE$$",                      LanguageDB["$loop-end"]],
                           ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                           ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                           ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                           ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("Skipper$$SKIPPER_INDEX$$[0]")],
                           ["$$ENDIF$$",                          LanguageDB["$endif"]],
                           ["$$ENTRY$$",                          LanguageDB["$label-def"]("$entry", skipper_index)],
                           ["$$DROP_OUT$$",                       LanguageDB["$label-def"]("$drop-out", skipper_index)],
                           ["$$GOTO_ENTRY$$",                     LanguageDB["$goto"]("$entry", skipper_index)],
                           # When things were skipped, no change to acceptance flags or modes has
                           # happend. One can jump immediately to the start without re-entry preparation.
                           ["$$GOTO_START$$",                     LanguageDB["$goto"]("$start")], 
                           ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                           ["$$ON_SKIP_RANGE_OPEN$$",             get_on_skip_range_open(Mode, EndSequence)],
                          ])
