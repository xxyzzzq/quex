/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__MEMORY_MANAGER_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__MEMORY_MANAGER_I__

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/plain/BufferFiller_Plain>
#include <quex/code_base/buffer/converter/BufferFiller_Converter>
#if defined (QUEX_OPTION_ENABLE_ICU)
#   include <quex/code_base/buffer/converter/icu/Converter_ICU>
#endif
#if defined (QUEX_OPTION_ENABLE_ICONV)
#   include <quex/code_base/buffer/converter/iconv/Converter_IConv>
#endif

#include <quex/code_base/temporary_macros_on>
 
#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex { 
#endif
    struct __QuexBufferFiller_tag;


    QUEX_INLINE QUEX_TYPE_CHARACTER*
    MemoryManager_BufferMemory_allocate(const size_t CharacterN)
    {
        return (QUEX_TYPE_CHARACTER*)__QUEX_ALLOCATE_MEMORY((size_t)(CharacterN * sizeof(QUEX_TYPE_CHARACTER)));
    }

    QUEX_INLINE void
    MemoryManager_BufferMemory_free(QUEX_TYPE_CHARACTER* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }

    TEMPLATE_IN(InputHandleT) TEMPLATED(QuexBufferFiller_Plain)*
    MemoryManager_BufferFiller_Plain_allocate()
    {
        const size_t     MemorySize = sizeof(TEMPLATED(QuexBufferFiller_Plain));
        return (TEMPLATED(QuexBufferFiller_Plain)*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    TEMPLATE_IN(InputHandleT) void
    MemoryManager_BufferFiller_Plain_free(TEMPLATED(QuexBufferFiller_Plain)* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }


    TEMPLATE_IN(InputHandleT) TEMPLATED(QuexBufferFiller_Converter)*
    MemoryManager_BufferFiller_Converter_allocate()
    {
        const size_t     MemorySize = sizeof(TEMPLATED(QuexBufferFiller_Converter));
        return (TEMPLATED(QuexBufferFiller_Converter)*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    TEMPLATE_IN(InputHandleT) void
    MemoryManager_BufferFiller_Converter_free(TEMPLATED(QuexBufferFiller_Converter)* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }

    QUEX_INLINE uint8_t*
    MemoryManager_BufferFiller_RawBuffer_allocate(const size_t ByteN)
    { return __QUEX_ALLOCATE_MEMORY(ByteN); }

    QUEX_INLINE void
    MemoryManager_BufferFiller_RawBuffer_free(uint8_t* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY(memory); }

#   if defined (QUEX_OPTION_ENABLE_ICONV)
    QUEX_INLINE QuexConverter_IConv*
    MemoryManager_Converter_IConv_allocate()
    {
        const size_t     MemorySize = sizeof(QuexConverter_IConv);
        return (QuexConverter_IConv*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    QUEX_INLINE void
    MemoryManager_Converter_IConv_free(QuexConverter_IConv* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }
#   endif

#   if defined (QUEX_OPTION_ENABLE_ICU)
    QUEX_INLINE QuexConverter_ICU*
    MemoryManager_Converter_ICU_allocate()
    {
        const size_t     MemorySize = sizeof(QuexConverter_ICU);
        return (QuexConverter_ICU*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }

    QUEX_INLINE void
    MemoryManager_Converter_ICU_free(QuexConverter_ICU* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }
#   endif

#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    QUEX_INLINE QUEX_TYPE_CHARACTER*
    MemoryManager_AccumulatorText_allocate(const size_t Size)
    {
        const size_t     MemorySize = Size * sizeof(QUEX_TYPE_CHARACTER);
        return (QUEX_TYPE_CHARACTER*)__QUEX_ALLOCATE_MEMORY(MemorySize);
    }
    QUEX_INLINE void
    MemoryManager_AccumulatorText_free(QUEX_TYPE_CHARACTER* memory)
    { if( memory != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)memory); }
#   endif

#   ifdef QUEX_OPTION_POST_CATEGORIZER
    QUEX_INLINE  QuexPostCategorizerNode*  
    MemoryManager_PostCategorizerNode_allocate(size_t RemainderL)
    {
        /* Allocate in one beat: base and remainder: 
         *
         *   [Base   |Remainder             ]
         *
         * Then bend the base->name_remainder to the Remainder part of the allocated
         * memory. Note, that this is not very efficient, since one should try to allocate
         * the small node objects and refer to the remainder only when necessary. This
         * would reduce cache misses.                                                      */
        const size_t   BaseSize  = sizeof(QuexPostCategorizerNode);
        /* Length + 1 == memory size (terminating zero) */
        const size_t   RemainderSize = sizeof(QUEX_TYPE_CHARACTER) * (RemainderL + 1);
        uint8_t*  base = __QUEX_ALLOCATE_MEMORY(BaseSize + RemainderSize);
        ((QuexPostCategorizerNode*)base)->name_remainder = (const QUEX_TYPE_CHARACTER*)(base + BaseSize);
        return (QuexPostCategorizerNode*)base;
    }

    QUEX_INLINE  void 
    MemoryManager_PostCategorizerNode_free(QuexPostCategorizerNode* node)
    { if( node != 0x0 ) __QUEX_FREE_MEMORY((uint8_t*)node); }
#   endif

    QUEX_INLINE size_t
    MemoryManager_insert(uint8_t* drain_begin_p,  uint8_t* drain_end_p,
                         uint8_t* source_begin_p, uint8_t* source_end_p)
        /* Inserts as many bytes as possible into the array from 'drain_begin_p'
         * to 'drain_end_p'. The source of bytes starts at 'source_begin_p' and
         * ends at 'source_end_p'.
         *
         * RETURNS: Number of bytes that have been copied.                      */
    {
        /* Determine the insertion size. */
        const size_t DrainSize = drain_end_p  - drain_begin_p;
        size_t       size      = source_end_p - source_begin_p;
        if( DrainSize < size ) size = DrainSize;

        /* memcpy() might fail if the source and drain domain overlap! */
#       ifdef QUEX_OPTION_ASSERTS 
        if( drain_begin_p > source_begin_p ) __quex_assert(drain_begin_p >= source_begin_p + size);
        else                                 __quex_assert(drain_begin_p <= source_begin_p - size);
#       endif
        __QUEX_STD_memcpy(drain_begin_p, source_begin_p, size);

        return size;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex
#endif
 
#include <quex/code_base/temporary_macros_off>

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__MEMORY_MANAGER_I__ */

