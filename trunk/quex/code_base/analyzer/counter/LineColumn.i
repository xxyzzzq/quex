/* -*- C++ -*-   vim: set syntax=cpp:
 * (C) Frank-Rene Schaefer                                                         */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_I

#if     defined(__QUEX_OPTION_COUNTER)
/* NOTE: Quex is pretty intelligent in choosing the right function
 *       to count line and column numbers. If, for example, a pattern
 *       does not contain newlines, then it simply adds the LexemeLength
 *       to the column number and does not do anything to the line number.
 *       Before touching anything in this code, first look at the generated
 *       code. The author of these lines considers it rather difficult to
 *       find better implementations of these functions in the framework
 *       of the generated engine.  <fschaef 07y6m30d>
 *
 * NOTE: Those functions are not responsible for setting the begin to the
 *       last end, such as base._line_number_at_begin = base._line_number_at_end.
 *       This has to happen outside these functions.                               */
#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/counter/LineColumn>
#include <quex/code_base/analyzer/asserts>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void
    CounterLineColumn_construct(CounterLineColumn* me, QUEX_NAME(AnalyzerData)* lexer)
    { 
#       ifdef QUEX_OPTION_ASSERTS
        /* Set all to '0xFF' in order to catch easily a lack of initialization. */
        memset((void*)me, 0xFF, sizeof(CounterLineColumn));
#       endif
        CounterBase_init((__CounterBase*)me); 

        /* The lexical analyzer is not important for this type of counter. */
    }

    QUEX_INLINE void
    CounterLineColumn_reset(CounterLineColumn* me)
    {
        CounterBase_init((__CounterBase*)me);
    }

    QUEX_INLINE void  
    CounterLineColumn_count_FixNewlineN(CounterLineColumn*             me,
                              QUEX_TYPE_CHARACTER* Lexeme,
                              QUEX_TYPE_CHARACTER* LexemeEnd,
                              const int            LineNIncrement) 
    {
        __quex_assert( LexemeEnd > Lexeme );
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        me->base._line_number_at_end += (size_t)LineNIncrement;
#       endif

#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __CounterLineColumn_count_chars_to_newline_backwards(me, (QUEX_TYPE_CHARACTER*)Lexeme, 
                                                   (QUEX_TYPE_CHARACTER*)(LexemeEnd), 
                                                   LexemeEnd - Lexeme,
                                                   /* LicenseToIncrementLineCountF = */ false);
#       endif
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }


    QUEX_INLINE QUEX_TYPE_CHARACTER*
    __CounterLineColumn_count_chars_to_newline_backwards(CounterLineColumn* me, 
                                             QUEX_TYPE_CHARACTER* Begin,
                                             QUEX_TYPE_CHARACTER* End,
                                             const ptrdiff_t      LexemeLength,
                                             const bool           LicenseToIncrementLineCountF /*=false*/)
    /* RETURNS: Pointer to the first newline or the beginning of the lexeme.
     *
     * This function increases base._line_number_at_end if a newline occurs and 
     * LicenseToIncrementLineCountF = true.
     *
     * NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
     *       from the following function or implemented unconditionally, since the decision
     *       is based, then on a condition of a constant (either true or false) -- once the 
     *       function has been inlined.   
     *
     * NOTE: Quex writes a call to this function only, if there **is** a potential
     *       newline in the lexeme. Otherwise, it adds the fixed pattern length
     *       or the LexemeLength directly.                                      */
    {
        __quex_assert(Begin < End);  /* LexemeLength >= 1 */

        /* loop from [End] to [Begin]:
         *
         *        [Begin]xxxxxxxxxxxxxxxxxxxxxxxxxx\n
         *     \n
         *     \n xxxxxxxxxxxxxxxxxxxxxxxx[End]
         *               <---------
         *                                                */
        QUEX_TYPE_CHARACTER* it = End - 1;
        for(; *it != '\n' ; --it) {
            if( it == Begin ) {
                /* -- in case NO newline occurs, the column index is to be INCREASED 
                 *    by the length of the string -1, since counting starts at zero
                 * -- base._column_number_at_begin =   base._column_number_at_end 
                 *                                   - LexemeLength (just take the old one) */
#               ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
                me->base._column_number_at_end += (size_t)LexemeLength;
#               endif
                return it;
            }
        }
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        /* -- in case that newline occurs, the column index is equal to
         *    the number of letters from newline to end of string             */
        __quex_assert(End >= it);
        me->base._column_number_at_end = (size_t)(End - it);
#       endif
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        if( LicenseToIncrementLineCountF ) ++(me->base._line_number_at_end);
#       endif
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
        return it;
    }

    QUEX_INLINE void    
    CounterLineColumn_count(CounterLineColumn* me, 
                            QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End)
    /* PURPOSE:
     *   Adapts the column number and the line number according to the newlines
     *   and letters of the last line occuring in the lexeme.
     *
     * NOTE: Providing LexemeLength may spare a subtraction (End - Lexeme) in case 
     *       there is no newline in the lexeme (see below).                        */
    {
        QUEX_TYPE_CHARACTER* it = __CounterLineColumn_count_chars_to_newline_backwards(me, Begin, End, End - Begin,
                                                                     /* LicenseToIncrementLineCountF = */ true);

#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        /* The last function may have digested a newline (*it == '\n'), but then it 
         * would have increased the base._line_number_at_end.                        */
        CounterBase_count_newline_n_backwards((__CounterBase*)me, it, Begin);
#       endif
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void  
    CounterLineColumn_count_NoNewline(CounterLineColumn* me, const ptrdiff_t LexemeLength) 
    {
        __quex_assert( LexemeLength > 0 );
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += (size_t)LexemeLength;
#       endif
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void 
    CounterLineColumn_print_this(CounterLineColumn* me)
    {
        CounterBase_print_this((__CounterBase*)me);
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/analyzer/counter/Base.i>

#endif /* defined(__QUEX_OPTION_COUNTER)     */
#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_I */
