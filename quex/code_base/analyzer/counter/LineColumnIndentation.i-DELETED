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
        QUEX_NAME(CounterBase_init)((QUEX_NAME(CounterBase)*)me);

        QUEX_NAME(IndentationStack_init)(&me->indentation_stack);
        me->indentation = 0;
        me->indentation_count_enabled_f = true;
        me->indentation_event_enabled_f = true;
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
        if( me->indentation_event_enabled_f ) {
            me->indentation = 0;
            QUEX_NAME(CounterLineColumnIndentation_on_indentation)(me);
        }
    }

    QUEX_INLINE void    
    QUEX_NAME(CounterLineColumnIndentation_count)(QUEX_NAME(CounterLineColumnIndentation)*   me,
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
         *             yes => start_consideration_it = Begin_it
         *             no  => perform normal line number and column number counting
         *                    (we are not in between newline and the first non-whitespace 
         *                     character of a line).
         *                    END
         *  
         *  (3) Count
         *  
         *      indentation  += number of whitespace between start_consideration_it 
         *                      and first non-whitespace character
         *      did non-whitespace character arrive?
         *         yes => indentation_counting = OFF
         *  
         *      column_number_at_end  = End_it - start_consideration_it
         *      line_number_at_end   += number of newlines from: Begin_it to: start_consideration_it
         *                                                                       */
        QUEX_TYPE_CHARACTER*  start_it = Lexeme;
        QUEX_TYPE_CHARACTER*  it       = Lexeme;

        __quex_assert(Lexeme < LexemeEnd);   /* LexemeLength >= 1: NEVER COMPROMISE THIS ! */

        for(it = Lexeme; it != LexemeEnd; ++it) {
            if( *it == '\n' ) {
                me->indentation_count_enabled_f = true;
                start_it = it;
            } else if( __QUEX_INDENTATION_CHECK_WHITESPACE(*it) == false ) {
                /* HERE: me->indentation_count_enabled_f == true  */
                /* Indentation WHITESPACE cannot contain newline! */
                /* A transition from indentation whitespace to non-whitespace detected !! */

                if( me->indentation_count_enabled_f ) {
                    /* Line and column number need to be counted before the indentation handler
                     * is called. This way it has to correct information.                     */
                    __QUEX_INDENTATION_ADD_CHUNK(me->indentation, (size_t)(it - start_it));

                    if( me->indentation_event_enabled_f ) {
                        QUEX_NAME(CounterLineColumnIndentation_on_indentation)(me);
                    } else {
                        me->indentation_event_enabled_f = true; /* Auto-enable for next time. */
                    }
                    /* Indentation counts only during first whitespace of a line. */
                    me->indentation_count_enabled_f = false;
                }

            } else {
                if( me->indentation_count_enabled_f ) {
                    __QUEX_INDENTATION_ADD_SINGLE(me->indentation, *it);
                }
                __QUEX_INDENTATION_ADD_SINGLE(me->base._column_number_at_end, *it);
            }
        }

        if( me->indentation_count_enabled_f ) {
            __QUEX_INDENTATION_ADD_CHUNK(me->indentation, (size_t)(it - start_it));
        }
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

#   if 0
    QUEX_INLINE void    
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline)(QUEX_NAME(CounterLineColumnIndentation)*  me,
                                                            QUEX_TYPE_CHARACTER*                      Lexeme,
                                                            const size_t                              LexemeL)
    /* Lexeme:    Pointer to first character of Lexeme.
     * LexemeEnd: Pointer to first character after Lexeme. */
    {
        /* NOTE: For an explanation of the algorithm, see the function:
         *       count_indentation(...).                                                   */
        QUEX_TYPE_CHARACTER* Begin = (QUEX_TYPE_CHARACTER*)Lexeme;

        /* (1) Last character == newline ? _______________________________________________
         *     [impossible, lexeme does never contain a newline]
         * (2) Find last newline in lexeme _______________________________________________
         *     [cannot be found]
         * (2.1) no newline in lexeme? [yes]                                               */
        if( me->indentation.count_enabled_f == false ) {
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
        QUEX_NAME(__CounterLineColumnIndentation_count_whitespace_to_first_non_whitespace)(me, 
                                                   Begin, 
                                                   Begin, 
                                                   Begin + LexemeL, 
                                                   /* LicenseToIncrementLineCountF = */ false);
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void  
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline_NeverStartOnWhitespace)(
                    QUEX_NAME(CounterLineColumnIndentation)*  me, 
                    const size_t                              ColumnNIncrement) 
    /* This is the fastest way to count: simply add the constant integer that represents 
     * the constant length of the lexeme (for patterns with fixed length, e.g. keywords). */
    {
        __quex_assert(ColumnNIncrement > 0);  /* lexeme length >= 1 */
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += ColumnNIncrement;
#       endif
        if( me->_indentation_count_enabled_f ) {
            me->_indentation_count_enabled_f = false; 
            QUEX_NAME(CounterLineColumnIndentation_on_indentation)(me);
        }
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }

    QUEX_INLINE void  
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline_ContainsOnlySpace)(
                                 QUEX_NAME(CounterLineColumnIndentation)*  me, 
                                 const size_t                              ColumnNIncrement) 
    {
        __quex_assert(ColumnNIncrement > 0);  /* lexeme length >= 1 */
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->base._column_number_at_end += ColumnNIncrement;
#       endif
        if( me->indentation.count_enabled_f ) me->indentation.count += ColumnNIncrement;
        __QUEX_LEXER_COUNT_ASSERT_CONSISTENCY();
    }
#endif

    QUEX_INLINE void      
    QUEX_NAME(CounterLineColumnIndentation_on_indentation)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
#       define self (*(me->_the_lexer))

        /* There should be at least the '0' indentation in place, thus: */
        __quex_assert(me->indentation_stack.end > me->indentation_stack.begin);

        /* Opening Indentation Block? */
        if( me->indentation > *(me->indentation_stack.end - 1) ) {
            self_send(QUEX_TKN_BLOCK_OPEN);
            QUEX_NAME(IndentationStack_push)(&me->indentation_stack, me->indentation);
            return;
        }

        /* Closing Indentation Block */
#       ifdef QUEX_OPTION_TOKEN_REPETITION_SUPPORT
        self_send_n(QUEX_TKN_CLOSE, 
                    QUEX_NAME(IndentationStack_pop_until)(&self.indentation_stack, Indentation));
#       else
        while( *(me->end - 1) > Indentation ) {
            self_send(QUEX_TKN_BLOCK_CLOSE);     
            QUEX_NAME(IndentationStack_pop)(&me->indentation_stack);
        }
#       endif

        /* Landing: Indentation has to fit indentation border. */
        if( *(me->end - 1) != Indentation ) {
            self_send(__QUEX_SETTING_TOKEN_ID_INDENTATION_ERROR);
        }

#       undef self
    }

    QUEX_INLINE void 
    QUEX_NAME(CounterLineColumnIndentation_print_this)(QUEX_NAME(CounterLineColumnIndentation)* me)
    {
        QUEX_NAME(CounterBase_print_this)((QUEX_NAME(CounterBase)*)me);
        __QUEX_STD_printf("   indentation                 = %i;\n", (int)me->indentation.count);
        __QUEX_STD_printf("   indentation.count_enabled_f = %s;\n", me->indentation_count_enabled_f ? "true" : "false");
        __QUEX_STD_printf("   indentation.event_enabled_f = %s;\n", me->indentation_event_enabled_f ? "true" : "false");
    }

    QUEX_INLINE void      
    QUEX_NAME(IndentationStack_init)(QUEX_NAME(IndentationStack)* me)
    {
        me->end        = me->begin;
        me->memory_end = me->begin + QUEX_SETTING_INDENTATION_STACK_SIZE;

        /* first indentation at column = 0 */
        IndentationStack_push(0);
        /* Default: Do not allow to open a sub-block. Constructs like 'for' loops
         * 'if' blocks etc. should allow the opening of an indentation.           */
        me->allow_opening_indentation_f = false;
    }


    QUEX_INLINE void
    QUEX_NAME(IndentationStack_push)(QUEX_NAME(IndentationStack)* me, uint16_t Indentation)
    {
        if( me->end == me->memory_end ) QUEX_ERROR_EXIT("Indentation stack overflow.");
        *(me->end++) = Indentation;
    }

    QUEX_INLINE void
    QUEX_NAME(IndentationStack_pop)(QUEX_NAME(IndentationStack)* me)
    {
        __quex_assert( me->end != me->begin );
        *(--(me->end));
    }

    QUEX_INLINE uint16_t
    QUEX_NAME(IndentationStack_pop_until)(QUEX_NAME(IndentationStack)* me, size_t Indentation)
    {
        uint16_t*  old_end_p = me->end;

        __quex_assert( me->end != me->begin );

        while( *(me->end - 1) > Indentation ) {
            *(--(me->end));
        }

        return old_end_p - me->end;
    }


QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/analyzer/counter/Base.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER__LINE_COLUMN_INDENTATION_I */
