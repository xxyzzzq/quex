/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer
 *
 * __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR may be undefined in case
 *    that multiple lexical analyzers are used. Then, the name of the
 *    QUEX_NAME(Accumulator) must be different.                             */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/Accumulator>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/token/TokenPolicy>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(Accumulator_init_memory)(QUEX_NAME(Accumulator)*   me) 
{
    me->text.begin      = \
        QUEX_NAME(MemoryManager_AccumulatorText_allocate)(
           QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE * sizeof(QUEX_TYPE_CHARACTER));
    if( me->text.begin == 0x0 ) {
        QUEX_ERROR_EXIT("Quex engine: out of memory--cannot allocate Accumulator.");
    }
    me->text.end        = me->text.begin;
    me->text.memory_end = me->text.begin + QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE;
}

QUEX_INLINE void
QUEX_NAME(Accumulator_construct)(QUEX_NAME(Accumulator)*   me, 
                                 QUEX_TYPE_ANALYZER*       lexer)
{
    me->the_lexer = lexer;
    QUEX_NAME(Accumulator_init_memory)(me);
}


QUEX_INLINE void
QUEX_NAME(Accumulator_destruct)(QUEX_NAME(Accumulator)* me)
{
    QUEX_NAME(MemoryManager_AccumulatorText_free)(me->text.begin);
    me->the_lexer       = 0x0;
    me->text.begin      = 0x0;
    me->text.end        = 0x0;
    me->text.memory_end = 0x0;
}

QUEX_INLINE bool
QUEX_NAME(Accumulator_extend)(QUEX_NAME(Accumulator)* me, size_t MinAddSize)
{
    const size_t  OldContentSize = (size_t)(me->text.end - me->text.begin);
    const size_t  Size    = (size_t)(me->text.memory_end - me->text.begin);
    const size_t  AddSize = (size_t)((float)Size * (float)QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR);
    const size_t  NewSize = Size + (AddSize < MinAddSize ? MinAddSize : AddSize);

    QUEX_TYPE_CHARACTER*  chunk = \
          QUEX_NAME(MemoryManager_AccumulatorText_allocate)(NewSize*sizeof(QUEX_TYPE_CHARACTER));

    if( chunk == 0x0 ) return false;

    __quex_assert(me->text.end >= me->text.begin);
    __quex_assert(me->text.memory_end >= me->text.begin);

    __QUEX_STD_memcpy(chunk, me->text.begin, sizeof(QUEX_TYPE_CHARACTER) * Size);

    QUEX_NAME(MemoryManager_AccumulatorText_free)(me->text.begin);

    me->text.begin      = chunk;
    me->text.end        = chunk + OldContentSize;
    me->text.memory_end = chunk + NewSize;
    return true;
}

QUEX_INLINE void
QUEX_NAME(Accumulator_clear)(QUEX_NAME(Accumulator)* me)
{
    /* If no text is to be flushed, return undone */
    if( me->text.begin == me->text.end ) return;
    me->text.end = me->text.begin;
}

QUEX_INLINE void 
QUEX_NAME(Accumulator_add)(QUEX_NAME(Accumulator)* me,
                           const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
{ 
    const size_t L = (size_t)(End - Begin);
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
        if( QUEX_NAME(Accumulator_extend)(me, L + 1) == false ) {
            QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
        }
    }

    __QUEX_STD_memcpy(me->text.end, Begin, L * sizeof(QUEX_TYPE_CHARACTER));
    me->text.end += L;
}


QUEX_INLINE void 
QUEX_NAME(Accumulator_add_character)(QUEX_NAME(Accumulator)*     me,
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
        if( QUEX_NAME(Accumulator_extend)(me, 2) == false ) {
            QUEX_ERROR_EXIT("Quex Engine: Out of Memory. Accumulator could not be further extended.\n");
        }
    }

    *(me->text.end) = Character;
    ++(me->text.end);
}

QUEX_INLINE void
QUEX_NAME(Accumulator_flush)(QUEX_NAME(Accumulator)*    me,
                             const QUEX_TYPE_TOKEN_ID  TokenID)
{
    /* All functions must ensure that there is one cell left to store the terminating zero. */
    __quex_assert(me->text.end < me->text.memory_end);


    /* If no text is to be flushed, return undone */
    if( me->text.begin == me->text.end ) return;

    *(me->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

#   define self (*me->the_lexer)
    QUEX_TOKEN_POLICY_SET_ID(TokenID);
    if( QUEX_NAMESPACE_TOKEN::QUEX_NAME_TOKEN(_take_text)(me, me->the_lexer, me->text.begin, me->text.end) ) {
        /* The called function does not need the memory chunk, we reuse it. */
        QUEX_NAME(Accumulator_clear)(me);
    } else {
        /* The called function wants to use the memory, so we get some new. */
        QUEX_NAME(Accumulator_init_memory)(me) 
    }
    QUEX_TOKEN_POLICY_PREPARE_NEXT();            
#   undef  self

}

QUEX_INLINE void  
QUEX_NAME(Accumulator_print_this)(QUEX_NAME(Accumulator)* me)
{
    /* All functions must ensure that there is one cell left to store the terminating zero. */
    __quex_assert(me->text.end < me->text.memory_end);

    *(me->text.end) = (QUEX_TYPE_CHARACTER)0; /* see above '__quex_assert()' */

    __QUEX_STD_printf("   Accumulator = '%s'\n", (const char*)me->text.begin);
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE void  
QUEX_NAME(Accumulator)::print_this()
{ QUEX_NAME(Accumulator_print_this)(this); }

QUEX_INLINE void
QUEX_NAME(Accumulator)::flush(const QUEX_TYPE_TOKEN_ID  TokenID)
{ QUEX_NAME(Accumulator_flush)(this, TokenID); }

QUEX_INLINE void 
QUEX_NAME(Accumulator)::add_chararacter(const QUEX_TYPE_CHARACTER  Character)
{ QUEX_NAME(Accumulator_add_character)(this, Character); }

QUEX_INLINE void 
QUEX_NAME(Accumulator)::add(const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
{ QUEX_NAME(Accumulator_add)(this, Begin, End); }

QUEX_INLINE void
QUEX_NAME(Accumulator)::clear()
{ QUEX_NAME(Accumulator_clear)(this); }
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/MemoryManager.i>
#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__ACCUMULATOR_I */
