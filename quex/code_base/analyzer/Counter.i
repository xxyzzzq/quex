// -*- C++ -*-   vim: set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__COUNTER_I__
#define __INCLUDE_GUARD__QUEX__COUNTER_I__
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
#include <quex/code_base/analyzer/Counter>
#include <quex/code_base/analyzer/count_common>

namespace quex { 

    inline
    Counter::Counter()
    { init(); }

    inline
    Counter::Counter(const Counter& That)
    {
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _line_number_at_begin = That._line_number_at_begin;   // line where current pattern starts
        _line_number_at_end   = That._line_number_at_end;     // line after current pattern
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _column_number_at_begin = That._column_number_at_begin;  // column where current pattern starts
        _column_number_at_end   = That._column_number_at_end;    // column after current pattern
#       endif
    }

    inline void
    Counter::init()
    {
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        _line_number_at_begin = (size_t)0;
        _line_number_at_end   = (size_t)1;
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _column_number_at_begin = (size_t)0;
        _column_number_at_end   = (size_t)1; 
#       endif
    }

    inline void    
    Counter::count(QUEX_TYPE_CHARACTER* Lexeme, QUEX_TYPE_CHARACTER* LexemeEnd)
    // PURPOSE:
    //   Adapts the column number and the line number according to the newlines
    //   and letters of the last line occuring in the lexeme.
    //
    // NOTE: Providing LexemeLength may spare a subtraction (End - Lexeme) in case 
    //       there is no newline in the lexeme (see below).
    //
    ////////////////////////////////////////////////////////////////////////////////
    {
#   if ! defined(QUEX_OPTION_COLUMN_NUMBER_COUNTING) && \
           ! defined(QUEX_OPTION_LINE_NUMBER_COUNTING)    
        return;
#   else
        QUEX_TYPE_CHARACTER* Begin = (QUEX_TYPE_CHARACTER*)Lexeme;
        QUEX_TYPE_CHARACTER* it = __count_chars_to_newline_backwards(Begin, LexemeEnd, LexemeEnd - Begin,
                                                                     /* LicenseToIncrementLineCountF = */ true);

#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        // The last function may have digested a newline (*it == '\n'), but then it 
        // would have increased the _line_number_at_end.
        __count_newline_n_backwards(it, Begin);
#       endif

        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
#   endif
    }

    inline void  
    Counter::count_NoNewline(const ptrdiff_t LexemeLength) 
    {
        __quex_assert( LexemeLength > 0 );

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _column_number_at_end += (size_t)LexemeLength;
#   endif

        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    inline void  
    Counter::count_FixNewlineN(QUEX_TYPE_CHARACTER* Lexeme,
                               QUEX_TYPE_CHARACTER* LexemeEnd,
                               const int            LineNIncrement) 
    {
        __quex_assert( LexemeEnd > Lexeme );
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        _line_number_at_end += (size_t)LineNIncrement;
#   endif

#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __count_chars_to_newline_backwards((QUEX_TYPE_CHARACTER*)Lexeme, 
                                           (QUEX_TYPE_CHARACTER*)(LexemeEnd), 
                                           LexemeEnd - Lexeme,
                                           /* LicenseToIncrementLineCountF = */ false);
#   endif
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }


    inline void
    Counter::__count_newline_n_backwards(QUEX_TYPE_CHARACTER* it,
                                         QUEX_TYPE_CHARACTER* Begin)
    // NOTE: If *it == '\n' this function does **not** count it. The user must
    //       have increased the _line_number_at_end by hisself. This happens
    //       for performance reasons.
    {
        __quex_assert(it >= Begin);
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        // investigate remaining part of the lexeme, i.e. before the last newline
        // (recall the lexeme is traced from the rear)
        while( it != Begin ) {
            --it;
            if( *it == '\n' ) ++_line_number_at_end; 
        }         
#   endif
    }

    inline QUEX_TYPE_CHARACTER*
    Counter::__count_chars_to_newline_backwards(QUEX_TYPE_CHARACTER* Begin,
                                                QUEX_TYPE_CHARACTER* End,
                                                const ptrdiff_t      LexemeLength,
                                                const bool           LicenseToIncrementLineCountF /*=false*/)
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
        return 0x0;
#else
        __quex_assert(Begin < End);                       // LexemeLength >= 1

        // loop from [End] to [Begin]:
        //
        //        [Begin]xxxxxxxxxxxxxxxxxxxxxxxxxx\n
        //     \n
        //     \n xxxxxxxxxxxxxxxxxxxxxxxx[End]
        //               <---------
        //
        QUEX_TYPE_CHARACTER* it = End - 1;
        for(; *it != '\n' ; --it) {
            if( it == Begin ) {
                // -- in case NO newline occurs, the column index is to be INCREASED 
                //    by the length of the string -1, since counting starts at zero
                // -- _column_number_at_begin = _column_number_at_end - LexemeLength (just take the old one)
#           ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
                _column_number_at_end += (size_t)LexemeLength;
#           endif
                return it;
            }
        }
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        // -- in case that newline occurs, the column index is equal to
        //    the number of letters from newline to end of string
        __quex_assert(End >= it);
        _column_number_at_end = (size_t)(End - it);
#   endif
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        if( LicenseToIncrementLineCountF ) ++_line_number_at_end;
#   endif
        return it;
#endif
    }

    inline void             
    Counter::__shift_end_values_to_start_values() 
    {
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        _line_number_at_begin   = _line_number_at_end;
#   endif
#   ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        _column_number_at_begin = _column_number_at_end;
#   endif
    }

    inline void 
    Counter::print_this()
    {
        __QUEX_STD_printf("   Counter:\n");
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            __QUEX_STD_printf("   _line_number_at_begin = %i;\n", (int)_line_number_at_begin);
            __QUEX_STD_printf("   _line_number_at_end   = %i;\n", (int)_line_number_at_end);
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            __QUEX_STD_printf("   _column_number_at_begin = %i;\n", (int)_column_number_at_begin);
            __QUEX_STD_printf("   _column_number_at_end   = %i;\n", (int)_column_number_at_end);
#       endif
    }

}
#endif /* __INCLUDE_GUARD__QUEX__COUNTER_I__ */
