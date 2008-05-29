// -*- C++ -*- vim:set syntax=cpp:

// (*) pure text accumulation and flushing
struct ACCUMULATOR_tag {
    // text buffer that eats **non-alien letters** until something 
    // occurs that makes a pure text token out of it.
    // (this can be a paragraph delimiter, or a command)
    ACCUMULATOR_tag($$LEXER_CLASS_NAME$$* lex) 
        : _the_lexer(lex) { _accumulated_text.reserve(1024); }
    void  flush(const $$TOKEN_CLASS$$::id_type TokenID);
    void  clear();
    void  add(const QUEX_LEXEME_CHARACTER_TYPE*);
    void  add(const QUEX_LEXEME_CHARACTER_TYPE);

private:
#    ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    int  _begin_line;
#    endif
#    ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    int  _begin_column;
#    endif
    std::basic_string<QUEX_LEXEME_CHARACTER_TYPE>  _accumulated_text;
    $$LEXER_CLASS_NAME$$*                          _the_lexer;     
};

inline void
ACCUMULATOR_tag::flush(const __QUEX_SETTING_TOKEN_CLASS_NAME::id_type TokenID)
{
    if( _accumulated_text.length() == 0 ) return;

    _the_lexer->send(TokenID, _accumulated_text.c_str());
    _accumulated_text = std::basic_string<QUEX_LEXEME_CHARACTER_TYPE>();
}


inline void
ACCUMULATOR_tag::clear()
{
    if( _accumulated_text.length() == 0 ) return;
    _accumulated_text = std::basic_string<QUEX_LEXEME_CHARACTER_TYPE>();
}

inline void 
ACCUMULATOR_tag::add(const QUEX_LEXEME_CHARACTER_TYPE* ToBeAppended)
{ 
    if( _accumulated_text.length() == 0 ) {
#     ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _begin_column = _the_lexer->column_number_at_begin();
#     endif
#     ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _begin_line   = _the_lexer->line_number_at_begin();
#     endif
    }
    _accumulated_text += ToBeAppended; 
}


inline void 
ACCUMULATOR_tag::add(const QUEX_LEXEME_CHARACTER_TYPE ToBeAppended)
{ 

#       if defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) || \
       defined(QUEX_OPTION_LINE_NUMBER_COUNTING)
    if( _accumulated_text.length() == 0 ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _begin_column = _the_lexer->column_number_at_begin();
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _begin_line   = _the_lexer->line_number_at_begin();
#           endif
    }
#       endif

    _accumulated_text += ToBeAppended; 
}

