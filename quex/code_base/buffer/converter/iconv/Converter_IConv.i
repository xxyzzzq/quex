/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICONV__CONVERTER_ICONV_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICONV__CONVERTER_ICONV_I

#ifndef __QUEX_OPTION_PLAIN_C
extern "C" { 
#endif
#include <errno.h>
#ifndef __QUEX_OPTION_PLAIN_C
}
#endif
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/iconv-argument-types.h>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/converter/iconv/Converter_IConv>

#if ! defined(QUEX_OPTION_CONVERTER_ICONV)
#    error "This header has been included without setting the compile option QUEX_OPTION_CONVERTER_ICONV. This could cause problems on systems where the correspondent headers are not installed. Make the inclusion of this header dependent on the above compile option."
#endif

#include <quex/code_base/analyzer/configuration/validation>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void 
    QUEX_NAME(Converter_IConv_open)(QUEX_NAME(Converter)* me,
                                    const char* FromCoding, const char* ToCoding);
    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_convert)(QUEX_NAME(Converter)*       me, 
                                       uint8_t**                   source, 
                                       const uint8_t*              SourceEnd,
                                       QUEX_TYPE_CHARACTER**       drain,  
                                       const QUEX_TYPE_CHARACTER*  DrainEnd);
    QUEX_INLINE void 
    QUEX_NAME(Converter_IConv_delete_self)(QUEX_NAME(Converter)* me);

    QUEX_INLINE QUEX_NAME(Converter)*
    QUEX_NAME(Converter_IConv_new)()
    {
        QUEX_NAME(Converter_IConv)*  me = \
           (QUEX_NAME(Converter_IConv)*)
           QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(Converter_IConv)),
                                          E_MemoryObjectType_CONVERTER);
        if( ! me ) {
            return (QUEX_NAME(Converter)*)0;
        }

        QUEX_NAME(Converter_construct)(&me->base,
                                       QUEX_NAME(Converter_IConv_open),
                                       QUEX_NAME(Converter_IConv_convert),
                                       QUEX_NAME(Converter_IConv_delete_self),
                                       (void (*)(struct QUEX_NAME(Converter_tag)*))0);

        me->handle = (iconv_t)-1;

        return &me->base;
    }

    QUEX_INLINE void 
    QUEX_NAME(Converter_IConv_open)(QUEX_NAME(Converter)* alter_ego,
                                    const char*           FromCoding, 
                                    const char*           ToCoding)
    {
        QUEX_NAME(Converter_IConv)* me = (QUEX_NAME(Converter_IConv)*)alter_ego;
#       if   defined(__QUEX_OPTION_LITTLE_ENDIAN)
        const bool little_endian_f = true;
#       elif defined(__QUEX_OPTION_BIG_ENDIAN)
        const bool little_endian_f = false;
#       elif defined(__QUEX_OPTION_SYSTEM_ENDIAN) 
        const bool little_endian_f = QUEXED(system_is_little_endian)();
#       endif

        /* Default: assume input encoding to have dynamic character sizes. */
        me->base.dynamic_character_size_f = true;
        me->base.virginity_f              = true;

        /* Setup conversion handle */
        if( ! ToCoding ) {
            switch( sizeof(QUEX_TYPE_CHARACTER) ) {
            case 4:  ToCoding = little_endian_f ? "UCS-4LE" : "UCS-4BE"; break;
            case 2:  ToCoding = little_endian_f ? "UCS-2LE" : "UCS-2BE"; break;
            case 1:  ToCoding = "ASCII"; break;
            default:  __quex_assert(false); return;
            }
        } 
        me->handle = iconv_open(ToCoding, FromCoding);

        if( me->handle == (iconv_t)-1 ) {
            /* __QUEX_STD_fprintf(stderr, "Source coding: '%s'\n", FromCoding);
             * __QUEX_STD_fprintf(stderr, "Target coding: '%s'\n", ToCoding);  */
            QUEX_ERROR_EXIT("<<IConv conversion: source or target character encoding name unknown.>>");
        }
    }

    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_convert)(QUEX_NAME(Converter)*  alter_ego, 
                                       uint8_t**              source, const uint8_t*              SourceEnd,
                                       QUEX_TYPE_CHARACTER**  drain,  const QUEX_TYPE_CHARACTER*  DrainEnd)
    {
        QUEX_NAME(Converter_IConv)* me = (QUEX_NAME(Converter_IConv)*)alter_ego;
        QUEX_TYPE_CHARACTER*        drain_begin = *drain;
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
        size_t  source_bytes_left_n = (size_t)(SourceEnd - *source);
        size_t  drain_bytes_left_n  = (size_t)(DrainEnd - *drain)*sizeof(QUEX_TYPE_CHARACTER);
        size_t  report;

        __quex_assert(me);
        __quex_assert(SourceEnd >= *source);
        __quex_assert(DrainEnd >= *drain);

        report = iconv(me->handle, 
                       __QUEX_ADAPTER_ICONV_2ND_ARG(source), &source_bytes_left_n,
                       (char**)drain,                        &drain_bytes_left_n);

        /* Check for BOM and, if necessary move it away (safety measure).    */
        if( *drain != drain_begin && drain_begin[0] == 0xfeff )
        {
            if( ! me->base.virginity_f ) {
                QUEX_ERROR_EXIT("Converter 'IConv' produced BOM upon not-first call to 'convert'\n"
                                "Better make sure that converter NEVER produces BOM.\n"
                                "(May be, by specifiying the endianness of 'FromCoding' or 'ToCoding')\n");
            }
            __QUEX_STD_memmove(&drain_begin[0], &drain_begin[1], 
                               ((size_t)(*drain - &drain_begin[1])) * sizeof(QUEX_TYPE_CHARACTER)); 
            *drain = &(*drain)[-1];
        }

        if( report != (size_t)-1 ) { 
            __quex_assert(source_bytes_left_n == 0);
            /* The input sequence (raw buffer content) has been converted 
             * completely. But, is the user buffer filled to its limits?     */
            if( drain_bytes_left_n == 0 ) {
                __quex_assert(*drain == DrainEnd);
                return true; 
            }
            else if( *source != SourceEnd ) {
                /* If the buffer was not filled completely, then was it because
                 * we reached EOF?  NOTE: Here, 'source->iterator' points to
                 * the position after the last byte that has been converted. If
                 * this is the end of the buffer, then it means that the raw
                 * buffer was read. If not, it means that the buffer has not
                 * been filled to its border which happens only if End of File
                 * occured.                                                  */
                return true;
            }
            else {

                /* Else: The user buffer is still hungry, thus the raw buffer
                 * needs more bytes. *source == SourceEnd anyway, so 'refill'
                 * is triggered at any time.                                 */
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
            return *drain == DrainEnd ? true : false;

        case E2BIG:
            /* The input buffer was not able to hold the number of converted characters.
             * (in other words we're filled up to the limit and that's what we actually wanted.) */
            return true;
        }
    }

    QUEX_INLINE void 
    QUEX_NAME(Converter_IConv_delete_self)(QUEX_NAME(Converter)* alter_ego)
    {
        QUEX_NAME(Converter_IConv)* me = (QUEX_NAME(Converter_IConv)*)alter_ego;

        iconv_close(me->handle); 
        QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_CONVERTER);
    }

QUEX_NAMESPACE_MAIN_CLOSE


#endif /* __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICONV__CONVERTER_ICONV_I */
