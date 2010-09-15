from   quex.frs_py.string_handling                   import blue_print
from   quex.input.setup                              import setup as Setup
import quex.core_engine.state_machine.index          as     sm_index
import quex.core_engine.generator.state_coder.transition_block as transition_block
from   quex.core_engine.interval_handling            import Interval

import sys

class IndentationCounter:
    def __init__(self, Type, Number):
        self.type   = Type
        self.number = Number

    def __eq__(self, Other):
        if Other.__class__ != IndentationCounter: return False
        return self.type == Other.type and self.number == Other.number

    def __ne__(self, Other):
        return not self.__eq__(Other)


template_str = """
{ 
    $$DELIMITER_COMMENT$$
$$INIT_REFERENCE_POINTER$$

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

$$LOOP_START$$
    $$INPUT_GET$$ 
$$ON_TRIGGER_SET_TO_LOOP_START$$
$$LOOP_REENTRANCE$$
    $$INPUT_P_INCREMENT$$ /* Now, BLC cannot occur. See above. */
    $$GOTO_LOOP_START$$

$$DROP_OUT$$
    /* -- In the case of 'skipping' we did not worry about the lexeme at all --
     *    HERE, WE DO! We cannot set the lexeme start point to the current position!
     *    The appplication might actuall do something with it.
     *
     * -- The input_p will at this point in time always point to the buffer border.  */
    if( $$INPUT_EQUAL_BUFFER_LIMIT_CODE$$ ) {
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
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
    # If the indentation consists only of spaces, than it is 'uniform' ...
    if IndentationSetup.has_only_single_spaces():
        # Count indentation/column at end of run;
        # simply: current position - reference_p

        character_set = IndentationSetup.space_db.values()[0]
        for interval in character_set.get().get_intervals(PromiseToTreatWellF=True):
            trigger_map.append([interval, counter_index])

        # Reference Pointer: Define Variable, Initialize, determine how to subtact.
        end_procedure     = \
        "    me->counter._indentation = (size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer) - reference_p);\n" 
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
        #                    (however, we pass 'reference_p' to indentation handler)
        end_procedure     = "" 

    # Since we do not use a 'TransitionMap', there are some things we need 
    # to som certain things by hand.
    arrange_trigger_map(trigger_map)

    local_variable_db = { "reference_p" : 
                          [ "QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER_POSITION)0x0", None] }
    init_reference_p  = "    reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);\n" + \
                        "    me->counter._indentation = (QUEX_TYPE_INDENTATION)0;\n"

    iteration_code = "".join(transition_block.do(trigger_map, counter_index, DSM=None))

    comment_str    = LanguageDB["$comment"]("Skip whitespace at line begin; count indentation.")

    # NOTE: Line and column number counting is off
    #       -- No newline can occur
    #       -- column number = indentation at the end of the process

    end_procedure += "    __QUEX_IF_COUNT_COLUMNS_ADD(me->counter._indentation);\n"
    end_procedure += "    QUEX_NAME(on_indentation)(me, me->counter._indentation, reference_p);\n"

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
                       ["$$ON_TRIGGER_SET_TO_LOOP_START$$",   iteration_code],
                       ["$$INIT_REFERENCE_POINTER$$",         init_reference_p],
                       ["$$END_PROCEDURE$$",                  end_procedure],
                      ])

    txt = blue_print(txt,
                     [["$$GOTO_DROP_OUT$$", LanguageDB["$goto"]("$drop-out", counter_index)]])

    return txt, local_variable_db

def arrange_trigger_map(trigger_map):
     """Arrange the trigger map: Sort, and insert 'drop-out-regions'
     """
     #  -- sort by interval
     trigger_map.sort(lambda x, y: cmp(x[0].begin, y[0].begin))
     
     #  -- insert lower and upper 'drop-out-transitions'
     if trigger_map[0][0].begin != -sys.maxint: 
         trigger_map.insert(0, [Interval(-sys.maxint, trigger_map[0][0].begin), None])
     if trigger_map[-1][0].end != sys.maxint: 
         trigger_map.append([Interval(trigger_map[-1][0].end, sys.maxint), None])

     #  -- fill gaps
     previous_end = -sys.maxint
     i    = 0
     size = len(trigger_map)
     while i < size:
         interval = trigger_map[i][0]
         if interval.begin != previous_end: 
             trigger_map.insert(i, [Interval(previous_end, interval.begin), None])
             i    += 1
             size += 1
         i += 1
         previous_end = interval.end

