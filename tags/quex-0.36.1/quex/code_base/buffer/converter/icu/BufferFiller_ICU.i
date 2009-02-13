/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICU_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICU_I__

#include <quex/code_base/buffer/converter/BufferFiller_Converter>
#include <quex/code_base/buffer/converter/icu/BufferFiller_ICU>
#include <quex/code_base/buffer/converter/icu/Converter_ICU>

#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE bool 
    __QuexBufferFiller_Converter_ICU_has_coding_dynamic_character_width(const char* Coding);


    TEMPLATE_IN(InputHandleT) TEMPLATED(QuexBufferFiller_Converter)* 
    QuexBufferFiller_Converter_ICU_new(InputHandleT* input_handle, 
                                       const char*   FromCoding,   const char* ToCoding,
                                       size_t        RawBufferSize)
    { 
        const bool ConstantCodingF = ! __QuexBufferFiller_Converter_ICU_has_coding_dynamic_character_width(FromCoding);

        return QuexBufferFiller_Converter_new(input_handle,
                                              QuexConverter_ICU_new(),
                                              FromCoding, ToCoding,
                                              RawBufferSize,
                                              ConstantCodingF);
                                             
    }

    QUEX_INLINE bool 
    __QuexBufferFiller_Converter_ICU_has_coding_dynamic_character_width(const char* Coding) 
    {
        return true; /* TODO: distinguish between different coding formats   */
        /*           //       'true' is safe, but possibly a little slower.  */
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
}
#endif

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/converter/icu/Converter_ICU.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICU_I__ */
