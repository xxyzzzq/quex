from   quex.frs_py.string_handling                   import blue_print
from   quex.input.setup                              import setup as Setup
import quex.core_engine.state_machine.index          as     sm_index
import quex.core_engine.generator.state_coder.transition_block as transition_block

class IndentationCounter:
    def __init__(self, Type, Number):
        self.type   = Type
        self.number = Number

template_str = """
{ 
    $$DELIMITER_COMMENT$$
$$INIT_REFERENCE_POINTER$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

    /* NOTE: For simple skippers the end of content does not have to be overwriten 
     *       with anything (as done for range skippers). This is so, because the abort
     *       criteria is that a character occurs which does not belong to the trigger 
     *       set. The BufferLimitCode, though, does never belong to any trigger set and
     *       thus, no special character is to be set.                                   */
$$LOOP_START$$
    $$INPUT_GET$$ 
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
        $$MARK_LEXEME_START$$
        if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
            $$GOTO_TERMINAL_EOF$$
        } else {
            QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                                   post_context_start_position, PostContextStartPositionN);

            QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
            $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
            $$GOTO_LOOP_START$$
        } 
    }

$$DROP_OUT_DIRECT$$
    /* No need for re-entry preparation. Acceptance flags and modes are untouched. */
    $$END_PROCEDURE$$                           
    $$GOTO_START$$                           
}
"""

def do(IndentationSetup):
    """The generated code is very similar to the 'skipper' code. It is to be executed
       as soon as a 'real' newline arrived. Then it skips whitespace until the next 
       non-whitepace (also newline may trigger a 'stop'). 

       Dependent on the setup the indentation is determined.
    """
    assert IndentationSetup.__class__.__name__ == "IndentationSetup"

    LanguageDB    = Setup.language_db

    counter_index = sm_index.get()
    
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.

    trigger_map = []
    if IndentationSetup.has_only_single_spaces():
        # Count indentation/column at end of run;
        # simply: current position - reference_p

        character_set = IndentationSetup.space_db.values()[0]
        for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
            trigger_map.append([interval, counter_index])

        # Reference Pointer: Define Variable, Initialize, determine how to subtact.
        local_variable_db = { "reference_p" : 
                              [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", None, "CountColumns"] }
        init_reference_p  = "    reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);"
        end_procedure     = \
        "        self.counter._indentation = (size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer) - reference_p);\n" 
    else:
        # Count the indentation/column during the 'run'

        # Add the space counters
        for count, character_set in IndentationSetup.space_db.items():
            for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
                trigger_map.append([interval, IndentationCounter("space", count)])
        # Add the grid counters
        for count, character_set in IndentationSetup.grid_db.items():
            for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
                trigger_map.append([interval, IndentationCounter("grid", count)])

        # Reference Pointer: Not required.
        #                    No subtraction 'current_position - reference_p'.
        local_variable_db = {}
        end_procedure     = "" 
        init_reference_p  = "" 

    iteration_code = "".join(transition_block.do(trigger_map, counter_index, DSM=None))

    comment_str    = LanguageDB["$comment"]("Skip whitespace at line begin; count indentation.")

    # NOTE: Line and column number counting is off
    #       -- No newline can occur
    #       -- column number = indentation at the end of the process

    end_procedure += "        __QUEX_IF_COUNT_COLUMNS_ADD(self.counter._indentation);\n"
    end_procedure += "        QUEX_NAME(on_indentation)(self.counter._indentation, reference_p);\n"

    # The finishing touch
    txt = blue_print(template_str,
                      [
                       ["$$DELIMITER_COMMENT$$",              comment_str],
                       ["$$INPUT_P_INCREMENT$$",              LanguageDB["$input/increment"]],
                       ["$$INPUT_P_DECREMENT$$",              LanguageDB["$input/decrement"]],
                       ["$$INPUT_GET$$",                      LanguageDB["$input/get"]],
                       ["$$IF_INPUT_EQUAL_DELIMITER_0$$",     LanguageDB["$if =="]("SkipDelimiter$$COUNTER_INDEX$$[0]")],
                       ["$$ENDIF$$",                          LanguageDB["$endif"]],
                       ["$$LOOP_START$$",                     LanguageDB["$label-def"]("$input",    counter_index)],
                       ["$$GOTO_LOOP_START$$",                LanguageDB["$goto"]("$input",         counter_index)],
                       ["$$LOOP_REENTRANCE$$",                LanguageDB["$label-def"]("$entry",    counter_index)],
                       ["$$INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB["$BLC"]],
                       ["$$RESTART$$",                        LanguageDB["$label-def"]("$input",    counter_index)],
                       ["$$DROP_OUT$$",                       LanguageDB["$label-def"]("$drop-out", counter_index)],
                       ["$$DROP_OUT_DIRECT$$",                LanguageDB["$label-def"]("$drop-out-direct", counter_index)],
                       ["$$COUNTER_INDEX$$",                  repr(counter_index)],
                       ["$$GOTO_TERMINAL_EOF$$",              LanguageDB["$goto"]("$terminal-EOF")],
                       # When things were skipped, no change to acceptance flags or modes has
                       # happend. One can jump immediately to the start without re-entry preparation.
                       ["$$GOTO_START$$",                     LanguageDB["$goto"]("$start")], 
                       ["$$MARK_LEXEME_START$$",              LanguageDB["$mark-lexeme-start"]],
                       ["$$ON_TRIGGER_SET_TO_LOOP_START$$",   iteration_code],
                       ["$$INIT_REFERENCE_POINTER$$",         init_reference_p],
                       ["$$END_PROCEDURE$$",                  end_procedure],
                      ])

    txt = blue_print(txt,
                     [["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", counter_index)]])

    return txt, local_variable_db

