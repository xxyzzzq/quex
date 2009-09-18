/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_TYPE_ACCUMULATOR must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I__
#define __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I__

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/Accumulator>
#include <quex/code_base/MemoryManager>

QUEX_NAMESPACE_COMPONENTS_OPEN

    QUEX_INLINE void
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

    QUEX_INLINE void
    QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _destruct)(QUEX_TYPE_ACCUMULATOR* me)
    {
        MemoryManager_AccumulatorText_free(me->text.begin);
        me->the_lexer       = 0x0;
        me->text.begin      = 0x0;
        me->text.end        = 0x0;
        me->text.memory_end = 0x0;
    }

    QUEX_INLINE bool
    QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _extend)(QUEX_TYPE_ACCUMULATOR* me, size_t MinAddSize)
    {
        const size_t  OldContentSize = me->text.end - me->text.begin;
        const size_t  Size    = me->text.memory_end - me->text.begin;
        const size_t  AddSize = (size_t)((float)Size * (float)QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR);
        const size_t  NewSize = Size + (AddSize < MinAddSize ? MinAddSize : AddSize);

        QUEX_TYPE_CHARACTER*  chunk = MemoryManager_AccumulatorText_allocate(NewSize);
        if( chunk == 0x0 ) return false;

        __QUEX_STD_memcpy(chunk, me->text.begin, sizeof(QUEX_TYPE_CHARACTER) * Size);

        MemoryManager_AccumulatorText_free(me->text.begin);

        me->text.begin      = chunk;
        me->text.end        = chunk + OldContentSize;
        me->text.memory_end = chunk + NewSize;
        return true;
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
        __quex_assert(End > Begin);

        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( this->text.begin == this->text.end ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            this->_begin_column = this->the_lexer->counter.base._column_number_at_begin;
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            this->_begin_line   = this->the_lexer->counter.base._line_number_at_begin;
#           endif
        }
#       endif

        /* Ensure, that there is one more cell between end and .memory_end to store
         * the terminating zero for flushing or printing.                           */
        if( this->text.memory_end <= this->text.end + L ) {
            /* L + 1 we need space for the string + the terminating zero */
            if( QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _extend)(this, L + 1) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        __QUEX_STD_memcpy(this->text.end, Begin, L * sizeof(QUEX_TYPE_CHARACTER));
        this->text.end += L;
    }


    QUEX_INLINE void 
    QUEX_MEMFUNC(ACCUMULATOR, add_chararacter)(__QUEX_SETTING_THIS_POINTER
                                               const QUEX_TYPE_CHARACTER  Character)
    { 
        /* If it is the first string to be appended, the store the location */
#       ifdef __QUEX_OPTION_COUNTER
        if( this->text.begin == this->text.end ) {
#           ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            this->_begin_column = this->the_lexer->counter.base._column_number_at_begin;
#           endif
#           ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
            this->_begin_line   = this->the_lexer->counter.base._line_number_at_begin;
#           endif
        }
#       endif

        /* Ensure, that there is one more cell between end and .memory_end to store
         * the terminating zero for flushing or printing.                           */
        if( this->text.memory_end <= this->text.end + 1 ) {
            /* 1 + 1 we need space for the character + the terminating zero */
            if( QUEX_PREFIX(QUEX_TYPE_ACCUMULATOR, _extend)(this, 2) == false ) {
                QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
            }
        }

        *(this->text.end) = Character;
        ++(this->text.end);
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(ACCUMULATOR, flush)(__QUEX_SETTING_THIS_POINTER
                                     const QUEX_TYPE_TOKEN_ID  TokenID)
    {
        /* All functions must ensure that there is one cell left to store the terminating zero. */
        __quex_assert(this->text.end < this->text.memory_end);


        /* If no text is to be flushed, return undone */
        if( this->text.begin == this->text.end ) return;

        *(this->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

        this->the_lexer->send(TokenID, this->text.begin);

        QUEX_MEMCALL(ACCUMULATOR, clear)(__QUEX_SETTING_THIS_POINTER);
    }

    QUEX_INLINE void  
    QUEX_MEMFUNC(ACCUMULATOR, print_this)(__QUEX_SETTING_THIS_POINTER)
    {
        /* All functions must ensure that there is one cell left to store the terminating zero. */
        __quex_assert(this->text.end < this->text.memory_end);

        *(this->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

        __QUEX_STD_printf("   Accumulator = '%s'\n", (const char*)this->text.begin);
    }

QUEX_NAMESPACE_COMPONENTS_CLOSE

#include <quex/code_base/MemoryManager.i>
#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I__ */
