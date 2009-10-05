/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__DELETED_BUFFER_FILLER_ICU_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__DELETED_BUFFER_FILLER_ICU_I

#include <quex/code_base/buffer/converter/BufferFiller_Converter>
#include <quex/code_base/buffer/converter/icu/BufferFiller_ICU>
#include <quex/code_base/buffer/converter/icu/Converter_ICU>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_COMPONENTS_OPEN

    QUEX_INLINE bool 
    __QuexBufferFiller_Converter_ICU_has_coding_dynamic_character_width(const char* Coding) 
    {
        return true; /* TODO: distinguish between different coding formats   */
        /*           //       'true' is safe, but possibly a little slower.  */
    }

QUEX_NAMESPACE_COMPONENTS_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/icu/Converter_ICU.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__DELETED_BUFFER_FILLER_ICU_I */
