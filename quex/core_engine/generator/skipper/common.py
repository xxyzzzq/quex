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
