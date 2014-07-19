/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__MEMORY_MANAGER_I
#define __QUEX_INCLUDE_GUARD__MEMORY_MANAGER_I

#include <quex/code_base/definitions>

#include <quex/code_base/temporary_macros_on>
 
QUEX_NAMESPACE_LEXEME_NULL_OPEN
/* Required for unit tests on buffer and buffer filling. */
extern QUEX_TYPE_CHARACTER QUEX_LEXEME_NULL_IN_ITS_NAMESPACE; 
QUEX_NAMESPACE_LEXEME_NULL_CLOSE

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE uint8_t*
QUEX_NAME(MemoryManager_allocate)(const size_t ByteN, QUEX_MEMORY_OBJECT Type)
{
    uint8_t*  memory = (uint8_t*)__QUEX_STD_malloc((size_t)ByteN);
    (void)Type;
#   ifdef QUEX_OPTION_ASSERTS
    __QUEX_STD_memset((void*)memory, 0xFF, ByteN);
#   endif
    return memory;
}
       
QUEX_INLINE void 
QUEX_NAME(MemoryManager_free)(void* memory, QUEX_MEMORY_OBJECT Type)  
{ 
    (void)Type;
    /* The de-allocator shall never be called for LexemeNull object.     */
    __quex_assert( memory != (void*)&(QUEX_LEXEME_NULL) );
    if( memory != (void*)0 ) {
        __QUEX_STD_free(memory); 
    }
}

QUEX_INLINE size_t
QUEX_NAME(MemoryManager_insert)(uint8_t* drain_begin_p,  uint8_t* drain_end_p,
                                uint8_t* source_begin_p, uint8_t* source_end_p)
    /* Inserts as many bytes as possible into the array from 'drain_begin_p'
     * to 'drain_end_p'. The source of bytes starts at 'source_begin_p' and
     * ends at 'source_end_p'.
     *
     * RETURNS: Number of bytes that have been copied.                      */
{
    /* Determine the insertion size. */
    const size_t DrainSize = (size_t)(drain_end_p  - drain_begin_p);
    size_t       size      = (size_t)(source_end_p - source_begin_p);
    __quex_assert(drain_end_p  >= drain_begin_p);
    __quex_assert(source_end_p >= source_begin_p);

    if( DrainSize < size ) size = DrainSize;

    /* memcpy() might fail if the source and drain domain overlap! */
#       ifdef QUEX_OPTION_ASSERTS 
    if( drain_begin_p > source_begin_p ) __quex_assert(drain_begin_p >= source_begin_p + size);
    else                                 __quex_assert(drain_begin_p <= source_begin_p - size);
#       endif
    __QUEX_STD_memcpy(drain_begin_p, source_begin_p, size);

    return size;
}

QUEX_NAMESPACE_MAIN_CLOSE
 
#include <quex/code_base/temporary_macros_off>

#endif /*  __QUEX_INCLUDE_GUARD__MEMORY_MANAGER_I */

