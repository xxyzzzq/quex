/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICONV_I__

#include <quex/code_base/definitions>
#if ! defined(QUEX_OPTION_ENABLE_ICONV)
#    error "This header has been included without setting the compile option QUEX_OPTION_ENABLE_ICONV. This could cause problems on systems where the correspondent headers are not installed. Make the inclusion of this header dependent on the above compile option."
#endif

#include <quex/code_base/analyzer/configuration_validation>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE void 
    QuexConverter_IConv_open(QuexConverter_IConv* me,
                             const char* FromCoding, const char* ToCoding)
    {
        /* Default: assume input encoding to have dynamic character sizes. */
        me->base.dynamic_character_size_f = true;

        /* Setup conversion handle */
        if( ToCoding == 0 ) {
            switch( sizeof(QUEX_TYPE_CHARACTER) ) {
            default:  __quex_assert(false); return;
#           if   defined (__QUEX_OPTION_SYSTEM_ENDIAN) 
            case 4:  me->handle = iconv_open("UCS-4LE",  FromCoding);  break;
            case 2:  me->handle = iconv_open("UCS-2LE",  FromCoding);  break;
#           elif defined(__QUEX_OPTION_LITTLE_ENDIAN)
            case 4:  me->handle = iconv_open("UCS-4LE",  FromCoding);  break;
            case 2:  me->handle = iconv_open("UCS-2LE",  FromCoding);  break;
#           elif defined(__QUEX_OPTION_BIG_ENDIAN)
            case 4:  me->handle = iconv_open("UCS-4BE",  FromCoding);  break;
            case 2:  me->handle = iconv_open("UCS-2BE",  FromCoding);  break;
#           endif
            case 1:  me->handle = iconv_open("ASCII",    FromCoding);  break;
            }
        } else {
            me->handle = iconv_open(ToCoding, FromCoding);
        }

        if( me->handle == (iconv_t)-1 ) {
            char tmp[128];
            snprintf(tmp, 127, "Conversion '%s' --> '%s' is not supported by 'iconv'.\n", FromCoding, ToCoding);
            QUEX_ERROR_EXIT(tmp);
        }
    }

    QUEX_INLINE bool 
    QuexConverter_IConv_convert(QuexConverter_IConv*   me, 
                                uint8_t**              source, const uint8_t*              SourceEnd,
                                QUEX_TYPE_CHARACTER**  drain,  const QUEX_TYPE_CHARACTER*  DrainEnd)
    {
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
        size_t drain_bytes_left_n  = (DrainEnd - *drain)*sizeof(QUEX_TYPE_CHARACTER);

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
             * to the end of the buffer in front of the new buffer).                               
             * If it happens, that we just finished filling the drain buffer before this happend
             * than the 'read_characters()' function does not need to reload.                    */
            if( *drain == DrainEnd ) return true;
            else                     return false; 

        case E2BIG:
            /* The input buffer was not able to hold the number of converted characters.
             * (in other words we're filled up to the limit and that's what we actually wanted.) */
            return true;
        }
    }

    QUEX_INLINE void 
    QuexConverter_IConv_delete_self(QuexConverter_IConv* me)
    {
        iconv_close(me->handle); 
        MemoryManager_Converter_IConv_free(me);
    }

    QUEX_INLINE QuexConverter*
    QuexConverter_IConv_new()
    {
        QuexConverter_IConv*  me = MemoryManager_Converter_IConv_allocate();

        me->base.open        = (QuexConverterFunctionP_open)QuexConverter_IConv_open;
        me->base.convert     = (QuexConverterFunctionP_convert)QuexConverter_IConv_convert;
        me->base.delete_self = (QuexConverterFunctionP_delete_self)QuexConverter_IConv_delete_self;
        me->base.on_conversion_discontinuity = 0x0;

        me->handle = (iconv_t)-1;

        return (QuexConverter*)me;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
}
#endif


#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/MemoryManager.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICONV_I__ */
