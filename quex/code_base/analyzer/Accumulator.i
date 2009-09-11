/* -*- C++ -*- vim:set syntax=cpp:
 *
 * NO INCLUDE GUARDS -- THIS FILE MIGHT BE INCLUDED TWICE FOR MULTIPLE
 *                      LEXICAL ANALYZERS
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_ACCUMULATOR_I__       */

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    void
    QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _construct)(QUEX_TYPE_ACCUMULATOR* me, 
                                                   QUEX_TYPE_ANALYZER*    lexer)
    {
        me->the_lexer = lexer;
        me->text.begin      = MemoryManager_AccumulatorText_allocate(QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE);
        if( me->text.begin == 0x0 ) {
            QUEX_ERROR_EXIT("Quex engine: out of memory--cannot allocate Accumulator.");
        }
        me->text.end        = me->text.begin;
        me->text.memory_end = me->text.begin + QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE;
    }

    void
    QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _destruct)(QUEX_TYPE_ACCUMULATOR* me, 
                                                  QUEX_TYPE_ANALYZER*    lexer);

    QUEX_INLINE bool
    QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _extend)(QUEX_TYPE_ACCUMULATOR* me)
    {
        const float   Size    = me->text.memory_end - me->text.begin;
        const size_t  AddSize = (size_t)(Size * (float)QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR);
        const size_t  NewSize = AddSize <= 0 ? Size + 1 : Size + AddSize;

        QUEX_TYPE_CHARACTER*  chunk = MemoryManager_AccumulatorText_allocate(Size);
        if( chunk == 0x0 ) return false;

        __QUEX_STD_memcpy(chunk, me->text.begin, sizeof(QUEX_TYPE_CHARACTER) * NewSize);

        MemoryManager_AccumulatorText_free(me->text.begin);

        me->text.begin      = chunk;
        me->text.end        = chunk;
        me->text.memory_end = chunk + NewSize;
        return true;
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ACCUMULATOR, flush)(__QUEX_SETTING_THIS_POINTER
                                     const QUEX_TYPE_TOKEN_ID  TokenID)
    {
        /* If no text is to be flushed, return undone */
        if( this->text.begin == this->text.end ) return;

        this->the_lexer->send(TokenID, this->text.begin);

        QUEX_MEMCALL(ACCUMULATOR, clear)(__QUEX_SETTING_THIS_POINTER);
    }


    QUEX_INLINE void
    QUEX_MEMFUNC(ACCUMULATOR, clear)(__QUEX_SETTING_THIS_POINTER)
    {
        /* If no text is to be flushed, return undone */
        if( this->text.begin == this->text.end ) return;
        this->text.end = this->text.begin;
    }

    QUEX_INLINE void 
    QUEX_MEMFUNC(ACCUMULATOR, add)(__QUEX_SETTING_THIS_POINTER
                                   const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
    { 
        const size_t L = End - Begin;

        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( this->text.begin == this->text.end ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _begin_column = this->the_lexer->counter.base._column_number_at_begin;
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            _begin_line   = this->the_lexer->counter.base._line_number_at_begin;
#           endif
        }
#       endif

        if( (size_t)(this->text.memory_end - this->text.end) < L ) {
            if( QUEX_MEMCALL(QUEX_TYPE_ACCUMULATOR, extend)(this) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        __QUEX_STD_memcpy(this->text.end, Begin, L * sizeof(QUEX_TYPE_CHARACTER));
        this->text.end += L;
    }


    QUEX_INLINE void 
    QUEX_MEMFUNC(ACCUMULATOR, add)(__QUEX_SETTING_THIS_POINTER
                                   const QUEX_TYPE_CHARACTER  Character)
    { 
        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( this->text.begin == this->text.end ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            _begin_column = this->the_lexer->counter.base._column_number_at_begin;
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            _begin_line   = this->the_lexer->counter.base._line_number_at_begin;
#           endif
        }
#       endif

        if( this->text.memory_end == this->text.end ) {
            if( QUEX_MEMCALL(QUEX_TYPE_ACCUMULATOR, extend)(me) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        *(this->text.end) = Character;
        ++(this->text.end);
    }

    QUEX_INLINE void  
    QUEX_MEMFUNC(ACCUMULATOR, print_this)(__QUEX_SETTING_THIS_POINTER)
    {
        __QUEX_STD_printf("   Accumulator = '%s'\n", (const char*)this->text);
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex 
#endif

