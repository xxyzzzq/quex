// -*- C++ -*-   :vim set syntax=cpp:

// NOTE: Quex is pretty intelligent in choosing the right function
//       to count line and column numbers. If, for example, a pattern
//       does not contain newlines, then it simply adds the LexemeLength
//       to the column number and does not do anything to the line number.
//       Before touching anything in this code, first look at the generated
//       code. The author of these lines considers it rather difficult to
//       find better implementations of these functions in the framework
//       of the generated engine.  <fschaef 07y6m30d>
//
// NOTE: Those functions are not responsible for setting the begin to the
//       last end, such as _line_number_at_begin = _line_number_at_end.
//       This has to happen outside these functions.

inline void 
$$LEXER_CLASS_NAME$$::__count_assert_consistency()
{
    __quex_assert(_line_number_at_begin   <= _line_number_at_end);
    // if line number remained the same, then the column number **must** have increased.
    // there is not pattern of a length less than 1
    __quex_assert(_line_number_at_begin != _line_number_at_end || 
           _column_number_at_begin <  _column_number_at_end);
}

inline void             
$$LEXER_CLASS_NAME$$::__count_shift_end_values_to_start_values() 
{
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    _line_number_at_begin   = _line_number_at_end;
#   endif
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_begin = _column_number_at_end;
#   endif
}


inline void    
$$LEXER_CLASS_NAME$$::count(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                            const int        LexemeLength)
// PURPOSE:
//   Adapts the column number and the line number according to the newlines
//   and letters of the last line occuring in the lexeme.
//
// NOTE: Providing LexemeLength may spare a subtraction (End - Lexeme) in case 
//       there is no newline in the lexeme (see below).
//
////////////////////////////////////////////////////////////////////////////////
{
    __quex_assert( LexemeLength > 0 );
#if ! defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) && \
    ! defined(QUEX_OPTION_LINE_NUMBER_COUNTING)    
    return;
#else
    QUEX_CHARACTER_TYPE* Begin = (QUEX_CHARACTER_TYPE*)Lexeme;
    QUEX_CHARACTER_TYPE* it = __count_chars_to_newline_backwards(Begin, Begin + LexemeLength, LexemeLength,
                                                             /* LicenseToIncrementLineCountF = */ true);

#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    // The last function may have digested a newline (*it == '\n'), but then it 
    // would have increased the _line_number_at_end.
    __count_newline_n_backwards(it, Begin);
#   endif

    __count_assert_consistency();
#endif
}

inline void  
$$LEXER_CLASS_NAME$$::count_NoNewline(const int LexemeLength) 
{
    __quex_assert( LexemeLength > 0 );

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    _column_number_at_end += LexemeLength;
#   endif

    __count_assert_consistency();
}

inline void  
$$LEXER_CLASS_NAME$$::count_FixNewlineN(QUEX_LEXEME_CHARACTER_TYPE* Lexeme,
                                        const int           LexemeLength, 
                                        const int           LineNIncrement) 
{
    __quex_assert( LexemeLength > 0 );
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    _line_number_at_end += LineNIncrement;
#   endif

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    __count_chars_to_newline_backwards((QUEX_CHARACTER_TYPE*)Lexeme, 
                                       (QUEX_CHARACTER_TYPE*)(Lexeme + LexemeLength), 
                                       LexemeLength,
                                       /* LicenseToIncrementLineCountF = */ false);
#   endif

    __count_assert_consistency();
}


inline void
$$LEXER_CLASS_NAME$$::__count_newline_n_backwards(QUEX_CHARACTER_TYPE* it,
                                                  QUEX_CHARACTER_TYPE* Begin)
// NOTE: If *it == '\n' this function does **not** count it. The user must
//       have increased the _line_number_at_end by hisself. This happens
//       for performance reasons.
{
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    // investigate remaining part of the lexeme, i.e. before the last newline
    // (recall the lexeme is traced from the rear)
    while( it != Begin ) {
        --it;
        if( *it == '\n' ) ++_line_number_at_end; 
    }         
#   endif
}

inline QUEX_CHARACTER_TYPE*
$$LEXER_CLASS_NAME$$::__count_chars_to_newline_backwards(QUEX_CHARACTER_TYPE* Begin,
                                                         QUEX_CHARACTER_TYPE* End,
                                                         const int        LexemeLength,
                                                         const bool       LicenseToIncrementLineCountF /*=false*/)
// RETURNS: Pointer to the first newline or the beginning of the lexeme.
//
// This function increases _line_number_at_end if a newline occurs and 
// LicenseToIncrementLineCountF = true.
//
// NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
//       from the following function or implemented unconditionally, since the decision
//       is based, then on a condition of a constant (either true or false) -- once the 
//       function has been inlined.   
//
// NOTE: Quex writes a call to this function only, if there **is** a potential
//       newline in the lexeme. Otherwise, it adds the fixed pattern length
//       or the LexemeLength directly.
{
#if ! defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) && \
    ! defined(QUEX_OPTION_LINE_NUMBER_COUNTING)    
    return;
#else
    __quex_assert(Begin >= __buffer->content_begin());
    __quex_assert(Begin < __buffer->content_end()-1); // LexemeLength >= 1
    __quex_assert(End <= __buffer->content_end());    // End > Lexeme follows from LexemeL > 0
    __quex_assert(Begin < End);                       // LexemeLength >= 1

    // loop from [End] to [Begin]:
    //
    //        [Begin]xxxxxxxxxxxxxxxxxxxxxxxxxx\n
    //     \n
    //     \n xxxxxxxxxxxxxxxxxxxxxxxx[End]
    //               <---------
    //
    QUEX_CHARACTER_TYPE* it = End - 1;
    for(; *it != '\n' ; --it) {
        if( it == Begin ) {
            // -- in case NO newline occurs, the column index is to be INCREASED 
            //    by the length of the string -1, since counting starts at zero
            // -- _column_number_at_begin = _column_number_at_end - LexemeLength (just take the old one)
            _column_number_at_end += LexemeLength;
            return it;
        }
    }
    // -- in case that newline occurs, the column index is equal to
    //    the number of letters from newline to end of string
    _column_number_at_end = End - it;
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
    if( LicenseToIncrementLineCountF ) ++_line_number_at_end;
#   endif
# endif
    return it;
}
