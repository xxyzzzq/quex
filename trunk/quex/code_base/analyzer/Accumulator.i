/* -*- C++ -*- vim:set syntax=cpp:
 *
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I__       */

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE void
    QUEX_MEMFUNC(ACCUMULATOR, flush)(QUEX_TYPE_ACCUMULATOR*    me, 
                                     const QUEX_TYPE_TOKEN_ID  TokenID)
    {
        /* If no text is to be flushed, return undone */
        if( me->text.begin == me->text.end == 0 ) return;

        _the_lexer->send(TokenID, me->text.begin);
        _accumulated_text = std::basic_string<QUEX_TYPE_CHARACTER>();
    }


    QUEX_INLINE void
    QUEX_MEMFUNC(ACCUMULATOR, clear)(QUEX_TYPE_ACCUMULATOR* me)
    {
        /* If no text is to be flushed, return undone */
        if( me->text.begin == me->text.end == 0 ) return;
        me->text.end = me->text.begin;
    }

    QUEX_INLINE void 
    QUEX_MEMFUNC(ACCUMULATOR, add)(QUEX_TYPE_ACCUMULATOR*     me, 
                                   const QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End)
    { 
        const L = End - Begin;

        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( me->text.begin == me->text.end == 0 ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _begin_column = _the_lexer->column_number_at_begin();
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            _begin_line   = _the_lexer->line_number_at_begin();
#           endif
        }
#       endif

        if( me->text.memory_end - me->text.end < L ) {
            if( QUEX_MEMFUNC_CALL(QUEX_TYPE_ACCUMULATOR, extend)(me) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        __QUEX_STD_memcpy(me->text.end, Begin, L * sizeof(QUEX_TYPE_CHARACTER));
        me->text.end += L;
    }


    QUEX_INLINE void 
    QUEX_MEMFUNC(ACCUMULATOR, add)(QUEX_TYPE_ACCUMULATOR*     me, 
                                   const QUEX_TYPE_CHARACTER  Character)
    { 
        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( me->text.begin == me->text.end == 0 ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _begin_column = _the_lexer->column_number_at_begin();
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            _begin_line   = _the_lexer->line_number_at_begin();
#           endif
        }
#       endif

        if( me->text.memory_end == me->text.end ) {
            if( QUEX_MEMFUNC_CALL(QUEX_TYPE_ACCUMULATOR, extend)(me) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        *(me->text.end) = Character;
        ++(me->text.end);
    }

    QUEX_INLINE void  
    QUEX_MEMFUNC(ACCUMULATOR, print_this)(QUEX_TYPE_ACCUMULATOR* me)
    {
        __QUEX_STD_printf("   Accumulator = '%s'\n", (const char*)me->text);
    }

    QUEX_INLINE bool
    QUEX_MEMFUNC(ACCUMULATOR, extend)(QUEX_TYPE_ACCUMULATOR* me)
    {
        const float   Size    = me->text.memory_end - me->text.begin;
        const size_t  AddSize = (size_t)(Size * (float)QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR);
        const size_t  NewSize = AddSize <= 0 ? Size + 1 : Size + AddSize;

        return QUEX_MEMFUNC_CALL(ACCUMULATOR, allocate_text)(me, NewSize);
    }

    QUEX_INLINE bool
    QUEX_MEMFUNC(ACCUMULATOR, allocate_text)(QUEX_TYPE_ACCUMULATOR* me, const size_t Size)
    {
        QUEX_TYPE_CHARACTER*  chunk = MemoryManager_AccumulatorText_allocate(Size);

        if( chunk == 0x0 ) return false;
        me->text.begin      = chunk;
        me->text.end        = chunk;
        me->text.memory_end = chunk + Size;
        return true;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex 
#endif

