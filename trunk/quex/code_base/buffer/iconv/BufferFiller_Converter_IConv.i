/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__
#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    TEMPLATE_IN(InputHandleT) void
    QuexBufferFiller_Converter_IConv_construct(TEMPLATED(QuexBufferFiller_IConv)* me,
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
                        ! __QuexBufferFiller_Converter_has_coding_dynamic_character_width(FromCoding);

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



    QUEX_INLINE void 
    QuexConverter_IConv_open(QuexConverter* alter_ego,
                             const char* FromCoding, const char* ToCoding)
    {
        QuexConverter_IConv* me = (QuexConverter_IConv*)alter_ego; 
        __quex_assert(me != 0x0);

        const char* to_coding = ToCoding != 0x0 ? ToCoding : QUEX_SETTING_CORE_ENGINE_DEFAULT_CHARACTER_CODING;

        me->handle = iconv_open(to_coding, FromCoding);
        if( me->handle == (iconv_t)-1 ) {
            char tmp[128];
            snprintf(tmp, 127, "Conversion '%s' --> '%s' is not supported by 'iconv'.\n", FromCoding, to_coding);
            QUEX_ERROR_EXIT(tmp);
        }
    }

    QUEX_INLINE bool 
    QuexConverter_IConv_convert(QuexConverter*   alter_ego, 
                                uint8_t**              source, const uint8_t*              SourceEnd,
                                QUEX_CHARACTER_TYPE**  drain,  const QUEX_CHARACTER_TYPE*  DrainEnd)
    {
        QuexConverter_IConv* me = (QuexConverter_IConv*)alter_ego; 
        /* RETURNS:  true  --> User buffer is filled as much as possible with converted 
         *                     characters.
         *           false --> More raw bytes are needed to fill the user buffer.           
         *
         *  IF YOU GET A COMPILE ERROR HERE, THEN PLEASE HAVE A LOOK AT THE FILE:
         *
         *      quex/code_base/compatibility/iconv-argument-types.h
         * 
         *  The issue is, that 'iconv' is defined on different systems with different
         *  types of the second argument. There are two variants 'const char**'
         *  and 'char **'.  If you get an error here, consider defining 
         *
         *            -DQUEX_SETTING_ICONV_2ND_ARG_CONST_CHARPP
         *
         *  as a compile option. If you have an elegant solution to solve the problem for 
         *  plain 'C', then please, let me know <fschaef@users.sourceforge.net>.               */
        size_t source_bytes_left_n = SourceEnd - *source;
        size_t drain_bytes_left_n  = (DrainEnd - *drain)*sizeof(QUEX_CHARACTER_TYPE);

        size_t report = iconv(me->handle, 
                              __QUEX_ADAPTER_ICONV_2ND_ARG(source), &source_bytes_left_n,
                              (char**)drain,                        &drain_bytes_left_n);

        if( report != (size_t)-1 ) { 
            __quex_assert(source_bytes_left_n == 0);
            /* The input sequence (raw buffer content) has been converted completely.
             * But, is the user buffer filled to its limits?                                   */
            if( drain_bytes_left_n == 0 ) {
                __quex_assert(*drain == DrainEnd);
                return true; 
            }
            /* If the buffer was not filled completely, then was it because we reached EOF?
             * NOTE: Here, 'source->iterator' points to the position after the last byte
             *       that has been converted. If this is the end of the buffer, then it means
             *       that the raw buffer was read. If not, it means that the buffer has not been
             *       filled to its border which happens only if End of File occured.           */
            if( *source != SourceEnd ) {
                /*__quex_assert(me->raw_buffer.end != me->raw_buffer.memory_end);*/
                return true;
            }
            else {
                /* Else: The user buffer is still hungry, thus the raw buffer needs more bytes. */
                /* *source == SourceEnd anyway, so 'refill' is triggered at any time.           */
                return false; 
            }
        }

        switch( errno ) {
        default:
            QUEX_ERROR_EXIT("Unexpected setting of 'errno' after call to GNU's iconv().");

        case EILSEQ:
            QUEX_ERROR_EXIT("Invalid byte sequence encountered for given character coding.");

        case EINVAL:
            /* Incomplete byte sequence for character conversion
             * ('raw_buffer.iterator' points to the beginning of the incomplete sequence.)
             * Please, refill the buffer (consider copying the bytes from raw_buffer.iterator 
             * to the end of the buffer in front of the new buffer).                             */
            return false; 

        case E2BIG:
            /* The input buffer was not able to hold the number of converted characters.
             * (in other words we're filled up to the limit and that's what we actually wanted.) */
            return true;
        }
    }

    QUEX_INLINE void 
    QuexConverter_IConv_delete_self(QuexConverter* alter_ego)
    {
        QuexConverter_IConv* me = (QuexConverter_IConv*)alter_ego; 
        iconv_close(me->handle); 
        MemoryManager_QuexConverter_IConv_free(me);
    }

    QUEX_INLINE QuexConverter*
    QuexConverter_IConv_new()
    {
        QuexConverter_IConv*  me = MemoryManager_QuexConverter_IConv_allocate();

        me->base.open        = QuexConverter_IConv_open;
        me->base.convert     = QuexConverter_IConv_convert;
        me->base.delete_self = QuexConverter_IConv_delete_self;

        me->handle = (iconv_t)-1;

        return (QuexConverter*)me;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
}
#endif

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__ */
