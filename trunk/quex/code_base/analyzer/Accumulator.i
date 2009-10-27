/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_TYPE_ACCUMULATOR must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/Accumulator>
#include <quex/code_base/MemoryManager>

#define QuexAccumulator_construct      QUEX_FIX(ACCUMULATOR, _construct)
#define QuexAccumulator_destruct       QUEX_FIX(ACCUMULATOR, _destruct)
#define QuexAccumulator_extend         QUEX_FIX(ACCUMULATOR, _extend)
#define QuexAccumulator_clear          QUEX_FIX(ACCUMULATOR, _clear)
#define QuexAccumulator_add            QUEX_FIX(ACCUMULATOR, _add)
#define QuexAccumulator_flush          QUEX_FIX(ACCUMULATOR, _flush)
#define QuexAccumulator_print_this     QUEX_FIX(ACCUMULATOR, _print_this)
#define QuexAccumulator_add_character  QUEX_FIX(ACCUMULATOR, _add_character)

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QuexAccumulator_construct(QUEX_TYPE_ACCUMULATOR* me, QUEX_TYPE_ANALYZER*    lexer)
{
    me->the_lexer       = lexer;
    me->text.begin      = MemoryManager_AccumulatorText_allocate(QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE);
    if( me->text.begin == 0x0 ) {
        QUEX_ERROR_EXIT("Quex engine: out of memory--cannot allocate Accumulator.");
    }
    me->text.end        = me->text.begin;
    me->text.memory_end = me->text.begin + QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE;
}

QUEX_INLINE void
QuexAccumulator_destruct(QUEX_TYPE_ACCUMULATOR* me)
{
    MemoryManager_AccumulatorText_free(me->text.begin);
    me->the_lexer       = 0x0;
    me->text.begin      = 0x0;
    me->text.end        = 0x0;
    me->text.memory_end = 0x0;
}

QUEX_INLINE bool
QuexAccumulator_extend(QUEX_TYPE_ACCUMULATOR* me, size_t MinAddSize)
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
QuexAccumulator_clear(QUEX_TYPE_ACCUMULATOR* me)
{
    /* If no text is to be flushed, return undone */
    if( me->text.begin == me->text.end ) return;
    me->text.end = me->text.begin;
}

QUEX_INLINE void 
QuexAccumulator_add(QUEX_TYPE_ACCUMULATOR* me,
                    const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
{ 
    const size_t L = End - Begin;
    __quex_assert(End > Begin);

    /* If it is the first string to be appended, the store the location */
#   ifdef __QUEX_OPTION_COUNTER
    if( me->text.begin == me->text.end ) {
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->_begin_column = me->the_lexer->counter.base._column_number_at_begin;
#       endif
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        me->_begin_line   = me->the_lexer->counter.base._line_number_at_begin;
#       endif
    }
#   endif

    /* Ensure, that there is one more cell between end and .memory_end to store
     * the terminating zero for flushing or printing.                           */
    if( me->text.memory_end <= me->text.end + L ) {
        /* L + 1 we need space for the string + the terminating zero */
        if( QUEX_FIX(ACCUMULATOR, _extend)(me, L + 1) == false ) {
            QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
        }
    }

    __QUEX_STD_memcpy(me->text.end, Begin, L * sizeof(QUEX_TYPE_CHARACTER));
    me->text.end += L;
}


QUEX_INLINE void 
QuexAccumulator_add_character(QUEX_TYPE_ACCUMULATOR*     me,
                              const QUEX_TYPE_CHARACTER  Character)
{ 
    /* If it is the first string to be appended, the store the location */
#   ifdef __QUEX_OPTION_COUNTER
    if( me->text.begin == me->text.end ) {
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        me->_begin_column = me->the_lexer->counter.base._column_number_at_begin;
#       endif
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        me->_begin_line   = me->the_lexer->counter.base._line_number_at_begin;
#       endif
    }
#   endif

    /* Ensure, that there is one more cell between end and .memory_end to store
     * the terminating zero for flushing or printing.                           */
    if( me->text.memory_end <= me->text.end + 1 ) {
        /* 1 + 1 we need space for the character + the terminating zero */
        if( QUEX_FIX(ACCUMULATOR, _extend)(me, 2) == false ) {
            QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
        }
    }

    *(me->text.end) = Character;
    ++(me->text.end);
}

QUEX_INLINE void
QuexAccumulator_flush(QUEX_TYPE_ACCUMULATOR*    me,
                      const QUEX_TYPE_TOKEN_ID  TokenID)
{
    /* All functions must ensure that there is one cell left to store the terminating zero. */
    __quex_assert(me->text.end < me->text.memory_end);


    /* If no text is to be flushed, return undone */
    if( me->text.begin == me->text.end ) return;

    *(me->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

    me->the_lexer->send(TokenID, me->text.begin);

    QUEX_FIX(ACCUMULATOR, _clear)(me);
}

QUEX_INLINE void  
QuexAccumulator_print_this(QUEX_TYPE_ACCUMULATOR* me)
{
    /* All functions must ensure that there is one cell left to store the terminating zero. */
    __quex_assert(me->text.end < me->text.memory_end);

    *(me->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

    __QUEX_STD_printf("   Accumulator = '%s'\n", (const char*)me->text.begin);
}

#ifndef __QUEX_SETTING_PLAIN_C
QUEX_INLINE void  
QUEX_TYPE_ACCUMULATOR::print_this()
{ QuexAccumulator_print_this(this); }

QUEX_INLINE void
QUEX_TYPE_ACCUMULATOR::flush(const QUEX_TYPE_TOKEN_ID  TokenID)
{ QuexAccumulator_flush(this, TokenID); }

QUEX_INLINE void 
QUEX_TYPE_ACCUMULATOR::add_chararacter(const QUEX_TYPE_CHARACTER  Character)
{ QuexAccumulator_add_character(this, Character); }

QUEX_INLINE void 
QUEX_TYPE_ACCUMULATOR::add(const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
{ QuexAccumulator_add(this, Begin, End); }

QUEX_INLINE void
QUEX_MEMFUNC(ACCUMULATOR, clear)()
{ QuexAccumulator_clear(this); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef QuexAccumulator_construct      
#undef QuexAccumulator_destruct       
#undef QuexAccumulator_extend         
#undef QuexAccumulator_clear          
#undef QuexAccumulator_add            
#undef QuexAccumulator_flush          
#undef QuexAccumulator_print_this     
#undef QuexAccumulator_add_character  

#include <quex/code_base/MemoryManager.i>
#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I */
