from   quex.input.setup import setup as Setup
import quex.core_engine.utf8         as utf8

line_counter_in_loop = """
#       if defined(QUEX_OPTION_LINE_NUMBER_COUNTING)
        if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
            __QUEX_IF_COUNT_LINES_ADD((size_t)1);
        }
#       endif
"""

line_column_counter_in_loop = """
#       if defined(QUEX_OPTION_LINE_NUMBER_COUNTING) || defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING)
        if( input == (QUEX_TYPE_CHARACTER)'\\n' ) { 
            __QUEX_IF_COUNT_LINES_ADD((size_t)1);
            __QUEX_IF_COUNT_COLUMNS_SET((size_t)0);
            __QUEX_IF_COUNT_COLUMNS(reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer));
        }
#       endif
"""

def get_character_sequence(Sequence):
    LanguageDB = Setup.language_db

    txt = ""
    comment_txt = ""
    for letter in Sequence:
        comment_txt += "%s, " % utf8.unicode_to_pretty_utf8(letter)
        txt += "0x%X, " % letter
    length_txt = "%i" % len(Sequence)

    return txt, length_txt, comment_txt

def end_delimiter_is_subset_of_indentation_counter_newline(Mode, EndSequence):
    indentation_setup = Mode.options().get("indentation")
    if indentation_setup == None: return False

    return indentation_setup.newline_state_machine().get().does_sequence_match(EndSequence)


def get_terminal_index_of_indentation_counter(Mode):
    """Returns the index of the terminal where the indentation counter 
       is implemented.
    """
    for info in Mode.get_pattern_action_pair_list():
        action = info.action()
        if action.__class__.__name__ != "GeneratedCode": continue
        action.function != indentation_counter.do: continue
        if info.action
