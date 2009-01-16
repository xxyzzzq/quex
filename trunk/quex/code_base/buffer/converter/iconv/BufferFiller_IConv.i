/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICONV_I__

#include <quex/code_base/buffer/converter/BufferFiller_Converter>
#include <quex/code_base/buffer/converter/iconv/BufferFiller_IConv>
#include <quex/code_base/buffer/converter/iconv/Converter_IConv>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/compatibility/iconv-argument-types.h>

#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE bool 
    __QuexBufferFiller_Converter_IConv_has_coding_dynamic_character_width(const char* Coding);


    TEMPLATE_IN(InputHandleT) void
    QuexBufferFiller_Converter_IConv_construct(TEMPLATED(QuexBufferFiller_Converter)* me,
                                               InputHandleT* input_handle, 
                                               const char*   FromCoding,   const char* ToCoding,
                                               size_t        RawBufferSize)
    { 
        const char* to_coding = ToCoding != 0x0 ? ToCoding : QUEX_SETTING_CORE_ENGINE_DEFAULT_CHARACTER_CODING;

        __quex_assert(RawBufferSize >= 6);  /* UTF-8 char can be 6 bytes long    */

        __QuexBufferFiller_init_functions(&me->base,
                                          TEMPLATED(QuexBufferFiller_Converter_tell_character_index),
                                          TEMPLATED(QuexBufferFiller_Converter_seek_character_index), 
                                          TEMPLATED(QuexBufferFiller_Converter_read_characters),
                                          TEMPLATED(QuexBufferFiller_Converter_destroy));

        me->ih = input_handle;

        /* Initialize the conversion operations                                             */
        me->converter = QuexConverter_IConv_new();
        me->converter->open(me->converter, FromCoding, to_coding);

        me->_constant_size_character_encoding_f = \
                        ! __QuexBufferFiller_Converter_IConv_has_coding_dynamic_character_width(FromCoding);

        /* Setup the tell/seek of character positions                                       */
        me->start_position    = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);

        /* Initialize the raw buffer that holds the plain bytes of the input file
         * (setup to trigger initial reload)                                                */
        uint8_t* raw_buffer_p = MemoryManager_get_BufferFiller_RawBuffer(RawBufferSize);
        __QuexRawBuffer_init(&me->raw_buffer, raw_buffer_p, RawBufferSize, 
                                               me->start_position);

        /* Hint for relation between character index, raw buffer offset and stream position */
        me->hint_begin_character_index = 0;

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_CONSTRUCTOR(FromCoding, ToCoding, me->iconv_handle);*/
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    QUEX_INLINE bool 
    __QuexBufferFiller_Converter_IConv_has_coding_dynamic_character_width(const char* Coding) 
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
#include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_FILLER_ICONV_I__ */
