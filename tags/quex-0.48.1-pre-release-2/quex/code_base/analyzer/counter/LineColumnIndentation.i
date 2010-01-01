/* -*- C++ -*-  vim:set syntax=cpp: 
 *
 * (C) 2004-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_INDENTATION_I may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_NAME(Accumulator) must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_INDENTATION_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_INDENTATION_I

#ifndef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT	
#   error "This file is only to be included, if indentation trigger support is activated."
#endif

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/counter/LineColumnIndentation>
#include <quex/code_base/analyzer/asserts>


QUEX_NAMESPACE_MAIN_OPEN

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
     *       last end, such as _line_number_at_begin = _line_number_at_end.
     *       This has to happen outside these functions.                        */
    QUEX_INLINE void
    QUEX_NAME(CounterLineColumnIndentation_construct)(QUEX_NAME(CounterLineColumnIndentation)* me, 
                                                      QUEX_TYPE_ANALYZER*                      lexer)
    {
#       ifdef QUEX_OPTION_ASSERTS
        /* Set all to '0xFF' in order to catch easily a lack of initialization. */
        memset((void*)me, 0xFF, sizeof(QUEX_NAME(CounterLineColumnIndentation)));
#       endif

        me->_the_lexer = lexer;

        QUEX_NAME(CounterLineColumnIndentation_init)(me);
    }

    QUEX_INLINE void
    QUEX_NAME(CounterLineColumnIndentation_init)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
        CounterBase_init((__CounterBase*)me);
        me->_indentation = 0;
        me->_indentation_count_enabled_f = true;
        me->_indentation_event_enabled_f = true;
    }

    QUEX_INLINE void
    QUEX_NAME(CounterLineColumnIndentation_reset)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
        QUEX_NAME(CounterLineColumnIndentation_init)(me);
    }


    QUEX_INLINE void
    QUEX_NAME(CounterLineColumnIndentation_on_end_of_file)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
        /* 'flush' remaining indentations                                      */
        if( me->_indentation_event_enabled_f ) 
            me->_the_lexer->__current_mode_p->on_indentation((QUEX_TYPE_ANALYZER*)me->_the_lexer, me->_indentation);
    }

    QUEX_INLINE void    
    QUEX_NAME(CounterLineColumnIndentation_icount)(QUEX_NAME(CounterLineColumnIndentation)*   me,
                                  QUEX_TYPE_CHARACTER*      Lexeme,
                                  QUEX_TYPE_CHARACTER*      LexemeEnd)
    /* Lexeme:    Pointer to first character of Lexeme.
     * LexemeEnd: Pointer to first character after Lexeme.
     *
     * PURPOSE:
     *   Adapts the column number and the line number according to the newlines
     *   and letters of the last line occuring in the lexeme.                  */
    {
        /*  NOTE: Indentation counting is only active between newline and the
         *        first non-whitespace character in a line. Use a variable
         *        to indicate the activation of newline.
         *  
         *  DEF: End_it   = pointer to first letter behind lexeme
         *       Begin_it = pointer to first letter of lexeme
         *  
         *  (1) last character of Lexeme == newline?
         *      yes => indentation_counting = ON
         *             indentation   = 0
         *             line_number_at_end   += number of newlines in Lexeme
         *             column_number_at_end  = 0           
         *      END
         *  
         *  (2) find last newline in Lexeme -> start_consideration_it
         *  
         *      (2.1) no newline in lexeme?
         *      yes => indentation_counting == ON ?
         *             no => perform normal line number and column number counting
         *                   (we are not in between newline and the first non-whitespace 
         *                    character of a line).
         *                   END
         *             yes => start_consideration_it = Begin_it
         *  
         *  (3) Count
         *  
         *      indentation  += number of whitespace between start_consideration 
         *                      and first non-whitespace character
         *      did non-whitespace character arrive?
         *         yes => indentation_counting = OFF
         *  
         *      column_number_at_end  = End_it - start_consideration_it
         *      line_number_at_end   += number of newlines from: Begin_it to: start_consideration_it
         *                                                                       */
        QUEX_TYPE_CHARACTER* Begin = (QUEX_TYPE_CHARACTER*)Lexeme;
        QUEX_TYPE_CHARACTER* Last  = LexemeEnd - 1;                
        QUEX_TYPE_CHARACTER* it    = Last;

        __quex_assert(Begin < LexemeEnd);   /* LexemeLength >= 1: NEVER COMPROMISE THIS ! */

        /* (1) Last character == newline ? _______________________________________________ */
        if( *Last == '\n' ) {
            me->_indentation = 0;
            me->_indentation_count_enabled_f = true;
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            ++(me->base._line_number_at_end);
            CounterBase_count_newline_n_backwards((__CounterBase*)me, it, Begin);
#           endif
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            me->base._column_number_at_end = 1;  /* next lexeme starts at _column_number_at_end + 1 */
#           endif
            __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
            return;
        }

        /* (2) Find last newline in lexeme _______________________________________________ */
        QUEX_TYPE_CHARACTER* start_consideration_it = 0x0;
        it = Last;
        while( it != Begin ) {
            /* recall assert: no lexeme with len(Lexeme) == 0 */
            --it;
            if( *it == '\n' ) { 		
                /* NOTE: according to the test in (1) it is not possible
                 *       that *it == "\n" and it == Last 
                 *       => there is always an iterator behind 'it'
                 *          if *it == "\n". The incrementation does
                 *          not need a check;                                             */
                start_consideration_it = it;
                ++start_consideration_it;  /* point to first character after newline      */
                me->_indentation = 0;
                me->_indentation_count_enabled_f = true;
#               ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
                me->base._column_number_at_end = 1;
#               endif
                break; 
            }	    
        }
        /* (2.1) no newline in lexeme? */
        if( start_consideration_it == 0x0 ) {
            if( me->_indentation_count_enabled_f == false ) {
                /* count increment without consideration of indentations
                 * no newline => no line number increment
                 *               no column number overflow / restart at '1'
                 * no indentation enabled => no indentation increment                     */
#               ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
                me->base._column_number_at_end += (size_t)(LexemeEnd - Begin);
#               endif
                return;
            }
            /* There was no newline, but the flag '_indentation_count_enabled_f'
             * tells us that before this pattern there was only whitespace after 
             * newline. Let us add the whitespace at the beginning of this pattern
             * to the _indentation.                                                       */
            start_consideration_it = Begin;
        }
        /* At this point:
         *   -- either there was no newline in the pattern, but the indentation
         *      count was active (see case above).
         *   -- or there was a newline in the pattern, so above it is set
         *      '_indentation_count_enabled_f = true'.                                    */
        __quex_assert( me->_indentation_count_enabled_f == true );

        /* (3) Count _____________________________________________________________________
         *
         * -- whitespace from: start_consideration to first non-whitespace
         *    (indentation count is disabled if non-whitespace arrives)                  */
        QUEX_NAME(__CounterLineColumnIndentation_count_whitespace_to_first_non_whitespace)(me, start_consideration_it, Begin, LexemeEnd, 
                                                   /* LicenseToIncrementLineCountF = */ true);

        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }


    QUEX_INLINE void    
    QUEX_NAME(CounterLineColumnIndentation_icount_NoNewline)(QUEX_NAME(CounterLineColumnIndentation)*  me,
                                            QUEX_TYPE_CHARACTER*     Lexeme,
                                            const int                LexemeL)
    /* Lexeme:    Pointer to first character of Lexeme.
     * LexemeEnd: Pointer to first character after Lexeme. */
    {
        /* NOTE: For an explanation of the algorithm, see the function:
         *       count_indentation(...).                                                    */
        QUEX_TYPE_CHARACTER* Begin = (QUEX_TYPE_CHARACTER*)Lexeme;

        /* (1) Last character == newline ? _______________________________________________
         *     [impossible, lexeme does never contain a newline]
         * (2) Find last newline in lexeme _______________________________________________
         *     [cannot be found]
         * (2.1) no newline in lexeme? [yes]                                               */
        if( me->_indentation_count_enabled_f == false ) {
            /* count increment without consideration of indentations
             * no newline => no line number increment
             *               no column number overflow / restart at '1'
             * no indentation enabled => no indentation increment       */
#           ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
            me->base._column_number_at_end += (size_t)LexemeL;
#           endif
            __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
            return;
        }
        
        /* The flag '_indentation_count_enabled_f' tells us that before this
         * pattern there was only whitespace after newline. Let us add the
         * whitespace at the beginning of this pattern to the _indentation. */
        QUEX_NAME(__CounterLineColumnIndentation_count_whitespace_to_first_non_whitespace)(me, Begin, Begin, Begin + LexemeL, 
                                                   /* LicenseToIncrementLineCountF = */ false);
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void  
    QUEX_NAME(CounterLineColumnIndentation_icount_NoNewline_NeverStartOnWhitespace)(QUEX_NAME(CounterLineColumnIndentation)* me, 
                                                                   const int ColumnNIncrement) 
    /* This is the fastest way to count: simply add the constant integer that represents 
     * the constant length of the lexeme (for patterns with fixed length, e.g. keywords). */
    {
        __quex_assert(ColumnNIncrement > 0);  // lexeme length >= 1
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += ColumnNIncrement;
#       endif
        if( me->_indentation_count_enabled_f ) {
            me->_indentation_count_enabled_f = false; 
            me->_the_lexer->__current_mode_p->on_indentation((QUEX_TYPE_ANALYZER*)me->_the_lexer, me->_indentation);
        }
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void  
    QUEX_NAME(CounterLineColumnIndentation_icount_NoNewline_ContainsOnlySpace)(QUEX_NAME(CounterLineColumnIndentation)*  me, 
                                                              const int                ColumnNIncrement) 
    {
        __quex_assert(ColumnNIncrement > 0);  /* lexeme length >= 1 */
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += ColumnNIncrement;
#       endif
        if( me->_indentation_count_enabled_f ) me->_indentation += ColumnNIncrement;
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void
    QUEX_NAME(__CounterLineColumnIndentation_count_whitespace_to_first_non_whitespace)(QUEX_NAME(CounterLineColumnIndentation)* me,
                                                                      QUEX_TYPE_CHARACTER* start_consideration_it, 
                                                                      QUEX_TYPE_CHARACTER* Begin,
                                                                      QUEX_TYPE_CHARACTER* End,
                                                                      const bool           LicenseToIncrementLineCountF)
    /* NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
     *       from the following function or implement it unconditionally, since the decision
     *       is based on a constant (either true or false) -- once the function has been inlined.  */ 
    {
        /* (3) Count _____________________________________________________________________
         *
         * -- whitespace from: start_consideration to first non-whitespace
         *    (indentation count is disabled if non-whitespace arrives) */
        QUEX_TYPE_CHARACTER* it = start_consideration_it;
        do { 
            if( *it != ' ' ) { 
                me->_indentation_count_enabled_f = false;
                me->_indentation += (size_t)(it - start_consideration_it);
                /* Line and column number need to be counted before the indentation handler
                 * is called. this way it has to correct information.                     */
                QUEX_NAME(CounterLineColumnIndentation_count_indentation_aux)(me, start_consideration_it, 
                                                             Begin, End, LicenseToIncrementLineCountF);
                /* indentation event enabled:
                 *   yes -> call indentation event handler
                 *   no  -> enable event for the next time.
                 *          indentation events can only be disabled for one coming event. */
                if( me->_indentation_event_enabled_f ) 
                    me->_the_lexer->__current_mode_p->on_indentation((QUEX_TYPE_ANALYZER*)me->_the_lexer, me->_indentation);
                else
                    /* event was disabled this time, enable it for the next time. */
                    me->_indentation_event_enabled_f = true;

                __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
                return;
            }
            ++it; 		    
        } while ( it != End );

        /* no non-whitespace until end of lexeme, thus only increment the indentation */
        me->_indentation += it - start_consideration_it;
        QUEX_NAME(CounterLineColumnIndentation_count_indentation_aux)(me, start_consideration_it, 
                                                     Begin, End, LicenseToIncrementLineCountF);
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void
    QUEX_NAME(CounterLineColumnIndentation_count_indentation_aux)(QUEX_NAME(CounterLineColumnIndentation)*  me,
                                                 QUEX_TYPE_CHARACTER*     start_consideration_it,
                                                 QUEX_TYPE_CHARACTER*     Begin,
                                                 QUEX_TYPE_CHARACTER*     End, 
                                                 const bool               LicenseToIncrementLineCountF)
    {
        /* when inlined, this is a condition on a constant => deleted by compiler. */
        if( LicenseToIncrementLineCountF ) {
#          ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
           CounterBase_count_newline_n_backwards((__CounterBase*)me, start_consideration_it, Begin);
#          endif	    
        }
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += End - start_consideration_it;
#       endif
    }

    QUEX_INLINE void 
    QUEX_NAME(CounterLineColumnIndentation_print_this)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
        CounterBase_print_this((__CounterBase*)me);
        __QUEX_STD_printf("   _indentation                 = %i;\n", (int)me->_indentation);
        __QUEX_STD_printf("   _indentation_count_enabled_f = %s;\n", me->_indentation_count_enabled_f ? "true" : "false");
        __QUEX_STD_printf("   _indentation_event_enabled_f = %s;\n", me->_indentation_event_enabled_f ? "true" : "false");
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/analyzer/counter/Base.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_INDENTATION_I */
