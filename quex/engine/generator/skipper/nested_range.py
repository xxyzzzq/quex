from   quex.engine.generator.skipper.common         import end_delimiter_is_subset_of_indentation_counter_newline, \
                                                           get_character_sequence, \
                                                           get_on_skip_range_open, \
                                                           line_column_counter_in_loop
import quex.engine.state_machine.index              as     sm_index
from   quex.blackboard                              import setup as Setup
from   quex.engine.misc.string_handling             import blue_print
from   quex.engine.analyzer.door_id_address_label   import __nice, dial_db
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.blackboard                              import E_StateIndices

def do(Data, Mode):

    OpeningSequence = Data["opener_sequence"]
    ClosingSequence = Data["closer_sequence"]

    return get_skipper(OpeningSequence, ClosingSequence, Mode=Mode) 

#def new_skipper():
#    #ClosingSequence = transform()
#    #OpeningSequence = transform()
#    character_set   = NumberSet(ClosingSequence[0])
#    character_set.add(OpeningSequence[0])
#    character_set.invert()
#
#    txt = "/* Assert sizeof(buffer) >= len(ClosingSequence) + 2 */\n"
#
#    end_sequence_check_adr = index.get()
#    end_sequence_label     = get_label("$entry", end_sequence_check_adr, U=True) 
#
#    implementation_type, \
#    loop_txt,            \
#    entry_action,        \
#    exit_action          = LoopGenerator.do(Mode.counter_db, 
#                             IteratorName = "me->buffer._input_p",
#                             OnContinue   = [ 1, "continue;" ],
#                             OnExit       = [ 1, "goto %s;" % end_sequence_label ],
#                             CharacterSet = character_set, 
#                             ReloadF      = True)
#
#    end_sequence_txt = get_end_sequence(OpeningSequence, ClosingSequence)

#def new_end_sequence():
#    txt.append("%s:\n" % EndSequenceLabel)
#    txt.append("/* Reload if necessary */\n")
#    txt.append("/* If fail --> skipped until end of file. */\n")
#    txt.append(LanguageDB.CHARACTER_BEGIN_P_SET())
#
#    common_sequence = common(OpeningSequence, ClosingSequence)
#    for chunk in common_sequence:
#        pass # Code if(chunk)
#
#    # 'if i == OpeningSequence[i]' --> continue with opening sequence
#    for chunk in common_sequence:
#        pass # Code if(chunk)
#
#    # 'if i == ClosingSequence[i]' --> continue with closing sequence

template_str = """
    Skipper$$SKIPPER_INDEX$$_Opener_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Opener;
    Skipper$$SKIPPER_INDEX$$_Closer_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Closer;
    /* text_end                           = QUEX_NAME(Buffer_text_end)(&me->buffer); */
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
        if( input == QUEX_SETTING_BUFFER_LIMIT_CODE ) {
            goto $$GOTO_RELOAD$$;
        }
        if( input == *Skipper$$SKIPPER_INDEX$$_Closer_it ) {
            ++Skipper$$SKIPPER_INDEX$$_Closer_it;
            if( Skipper$$SKIPPER_INDEX$$_Closer_it == Skipper$$SKIPPER_INDEX$$_CloserEnd ) {
                if( counter == 0 ) {
                    /* NOTE: The initial state does not increment the input_p. When it detects that
                     * it is located on a buffer border, it automatically triggers a reload. No 
                     * need here to reload the buffer. */
                    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
                    $$LC_COUNT_END_PROCEDURE$$
                    /* No need for re-entry preparation. Acceptance flags and modes are untouched after skipping. */
                    $$GOTO_AFTER_END_OF_SKIPPING$$ /* End of range reached. */
                }
                --counter;
                Skipper$$SKIPPER_INDEX$$_Opener_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Opener;
                Skipper$$SKIPPER_INDEX$$_Closer_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Closer;
                goto CONTINUE_$$SKIPPER_INDEX$$;
            }
        } else {
            Skipper$$SKIPPER_INDEX$$_Closer_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Closer;
        }
        if( input == *Skipper$$SKIPPER_INDEX$$_Opener_it ) {
            ++Skipper$$SKIPPER_INDEX$$_Opener_it;
            if( Skipper$$SKIPPER_INDEX$$_Opener_it == Skipper$$SKIPPER_INDEX$$_OpenerEnd ) {
                ++counter;
                Skipper$$SKIPPER_INDEX$$_Opener_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Opener;
                Skipper$$SKIPPER_INDEX$$_Closer_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Closer;
                goto CONTINUE_$$SKIPPER_INDEX$$;
            }
        } else {
            Skipper$$SKIPPER_INDEX$$_Opener_it = (QUEX_TYPE_CHARACTER*)Skipper$$SKIPPER_INDEX$$_Opener;
        }
CONTINUE_$$SKIPPER_INDEX$$:
$$LC_COUNT_IN_LOOP$$
        $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    }

$$RELOAD$$:
    QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(&me->buffer);
    /* -- When loading new content it is checked that the beginning of the lexeme
     *    is not 'shifted' out of the buffer. In the case of skipping, we do not care about
     *    the lexeme at all, so do not restrict the load procedure and set the lexeme start
     *    to the actual input position.                                                    */
    $$MARK_LEXEME_START$$

$$LC_COUNT_BEFORE_RELOAD$$
    if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) == false ) {
        QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)position,
                                         PositionRegisterN);
        /* Recover '_input_p' from lexeme start 
         * (inverse of what we just did before the loading) */
        $$INPUT_P_TO_LEXEME_START$$
        /* After reload, we need to increment _input_p. That's how the game is supposed to be played. 
         * But, we recovered from lexeme start pointer, and this one does not need to be incremented. */
        /* text_end = QUEX_NAME(Buffer_text_end)(&me->buffer); */
$$LC_COUNT_AFTER_RELOAD$$
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        $$GOTO_ENTRY$$ /* End of range reached.             */
    }
    /* Here, either the loading failed or it is not enough space to carry a closing delimiter */
    $$INPUT_P_TO_LEXEME_START$$
    $$ON_SKIP_RANGE_OPEN$$
"""

def get_skipper(OpenerSequence, CloserSequence, Mode=None, IndentationCounterTerminalID=None, OnSkipRangeOpenStr=""):
    assert OpenerSequence.__class__  == list
    assert len(OpenerSequence)       >= 1
    assert map(type, OpenerSequence) == [int] * len(OpenerSequence)
    assert CloserSequence.__class__  == list
    assert len(CloserSequence)       >= 1
    assert map(type, CloserSequence) == [int] * len(CloserSequence)
    assert OpenerSequence != CloserSequence

    LanguageDB    = Setup.language_db

    skipper_index = sm_index.get()

    opener_str, opener_comment_str = get_character_sequence(OpenerSequence)
    opener_length = len(OpenerSequence)
    closer_str, closer_comment_str = get_character_sequence(CloserSequence)
    closer_length = len(CloserSequence)

    if not end_delimiter_is_subset_of_indentation_counter_newline(Mode, CloserSequence):
        goto_after_end_of_skipping_str = LanguageDB.GOTO_BY_VARIABLE(E_StateIndices.ANALYZER_REENTRY)
    else:
        # If there is indentation counting involved, then the counter's terminal id must
        # be determined at this place.
        # If the ending delimiter is a subset of what the 'newline' pattern triggers 
        # in indentation counting => move on to the indentation counter.
        goto_after_end_of_skipping_str = LanguageDB.GOTO_TERMINAL_BY_INCIDENCE_ID(IncidenceID.INDENTATION_HANDLER)

    if OnSkipRangeOpenStr != "": on_skip_range_open_str = OnSkipRangeOpenStr
    else:                        on_skip_range_open_str = get_on_skip_range_open(Mode, CloserSequence)

    variable_db.require("reference_p", Condition="QUEX_OPTION_COLUMN_NUMBER_COUNTING")
    # variable_db.enter(local_variable_db, "text_end")
    variable_db.require("counter")
    variable_db.require_array("Skipper%i_Opener", Initial="{ %s }" % opener_str, ElementN=opener_length, Index = skipper_index)
    variable_db.require("Skipper%i_OpenerEnd", "Skipper%i_Opener + (ptrdiff_t)%i" % (skipper_index, opener_length), Index = skipper_index) 
    variable_db.require("Skipper%i_Opener_it", "0x0", Index = skipper_index) 
    variable_db.require_array("Skipper%i_Closer", Initial="{ %s }" % closer_str, ElementN=closer_length, Index = skipper_index) 
    variable_db.require("Skipper%i_CloserEnd", "Skipper%i_Closer + (ptrdiff_t)%i" % (skipper_index, closer_length), Index = skipper_index) 
    variable_db.require("Skipper%i_Closer_it", "0x0", Index = skipper_index) 

    reference_p_def = "    __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"
    before_reload   = "    __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                      "                                - reference_p));\n" 
    after_reload    = "        __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));\n"

    if CloserSequence[-1] == ord('\n'):
        end_procedure  = "       __QUEX_IF_COUNT_LINES_ADD((size_t)1);\n"
        end_procedure += "       __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n"
    else:
        end_procedure = "        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer)\n" + \
                        "                                    - reference_p));\n" 

    reload_door_id = dial_db.new_door_id()

    code_str = blue_print(template_str, [
                   ["$$SKIPPER_INDEX$$",   __nice(skipper_index)],
                   #
                   ["$$OPENER_LENGTH$$",                  "%i" % opener_length],
                   ["$$INPUT_P_INCREMENT$$",              LanguageDB.INPUT_P_INCREMENT()],
                   ["$$INPUT_P_DECREMENT$$",              LanguageDB.INPUT_P_DECREMENT()],
                   ["$$INPUT_GET$$",                      LanguageDB.ACCESS_INPUT()],
                   ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB.IF_INPUT("==", "Skipper$$SKIPPER_INDEX$$[0]")],
                   ["$$ENDIF$$",                          LanguageDB.END_IF()],
                   ["$$ENTRY$$",                          dial_db.map_address_to_label(skipper_adr)],
                   ["$$RELOAD$$",                         dial_db.get_label_by_door_id(reload_door_id)],
                   ["$$GOTO_AFTER_END_OF_SKIPPING$$",     goto_after_end_of_skipping_str], 
                   ["$$GOTO_RELOAD$$",                    LanguageDB.GOTO_RELOAD(reload_door_id)],
                   ["$$INPUT_P_TO_LEXEME_START$$",        LanguageDB.INPUT_P_TO_LEXEME_START()],
                   # When things were skipped, no change to acceptance flags or modes has
                   # happend. One can jump immediately to the start without re-entry preparation.
                   ["$$GOTO_ENTRY$$",                     LanguageDB.GOTOBY_DOOR_ID(skipper_index)],
                   ["$$MARK_LEXEME_START$$",              LanguageDB.LEXEME_START_SET()],
                   ["$$ON_SKIP_RANGE_OPEN$$",             on_skip_range_open_str],
                   #
                   ["$$LC_COUNT_COLUMN_N_POINTER_DEFINITION$$", reference_p_def],
                   ["$$LC_COUNT_IN_LOOP$$",                     line_column_counter_in_loop()],
                   ["$$LC_COUNT_END_PROCEDURE$$",               end_procedure],
                   ["$$LC_COUNT_BEFORE_RELOAD$$",               before_reload],
                   ["$$LC_COUNT_AFTER_RELOAD$$",                after_reload],
               ])

    return [ code_str ]


