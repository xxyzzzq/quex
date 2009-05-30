// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I
#define __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I

namespace quex { 
inline void
Accumulator::flush(const QUEX_TYPE_TOKEN_ID TokenID)
{
    if( _accumulated_text.length() == 0 ) return;

    _the_lexer->send(TokenID, _accumulated_text.c_str());
    _accumulated_text = std::basic_string<QUEX_TYPE_CHARACTER>();
}


inline void
Accumulator::clear()
{
    if( _accumulated_text.length() == 0 ) return;
    _accumulated_text = std::basic_string<QUEX_TYPE_CHARACTER>();
}

inline void 
Accumulator::add(const QUEX_TYPE_CHARACTER* ToBeAppended)
{ 
    if( _accumulated_text.length() == 0 ) {
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _begin_column = _the_lexer->column_number_at_begin();
#       endif
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _begin_line   = _the_lexer->line_number_at_begin();
#       endif
    }
    _accumulated_text += ToBeAppended; 
}


inline void 
Accumulator::add(const QUEX_TYPE_CHARACTER ToBeAppended)
{ 

#   if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) || \
    defined(QUEX_OPTION_LINE_NUMBER_COUNTING)
    if( _accumulated_text.length() == 0 ) {
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _begin_column = _the_lexer->column_number_at_begin();
#       endif
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _begin_line   = _the_lexer->line_number_at_begin();
#       endif
    }
#   endif

    _accumulated_text += ToBeAppended; 
}

} // namespace quex
#endif // __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I
