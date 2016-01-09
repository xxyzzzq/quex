/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__ICONV__CONVERTER_ICONV_I
#define  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__ICONV__CONVERTER_ICONV_I

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
#include <quex/code_base/buffer/lexatoms/converter/iconv/Converter_IConv>

#if ! defined(QUEX_OPTION_CONVERTER_ICONV)
#    error "This header has been included without setting the compile option QUEX_OPTION_CONVERTER_ICONV. This could cause problems on systems where the correspondent headers are not installed. Make the inclusion of this header dependent on the above compile option."
#endif

#include <quex/code_base/analyzer/configuration/validation>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_open)(QUEX_NAME(Converter)* me,
                                    const char* FromCodec, const char* ToCodec);
    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_convert)(QUEX_NAME(Converter)*       me, 
                                       uint8_t**                   source, 
                                       const uint8_t*              SourceEnd,
                                       QUEX_TYPE_CHARACTER**       drain,  
                                       const QUEX_TYPE_CHARACTER*  DrainEnd);
    QUEX_INLINE void 
    QUEX_NAME(Converter_IConv_delete_self)(QUEX_NAME(Converter)* me);

    QUEX_INLINE QUEX_NAME(Converter)*
    QUEX_NAME(Converter_IConv_new)(const char* FromCodec, const char* ToCodec)
    {
        QUEX_NAME(Converter_IConv)*  me = \
           (QUEX_NAME(Converter_IConv)*)
           QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(Converter_IConv)),
                                          E_MemoryObjectType_CONVERTER);
        if( ! me ) {
            return (QUEX_NAME(Converter)*)0;
        }

        me->handle = (iconv_t)-1;
        if( ! QUEX_NAME(Converter_construct)(&me->base,
                                             FromCodec, ToCodec,
                                             QUEX_NAME(Converter_IConv_open),
                                             QUEX_NAME(Converter_IConv_convert),
                                             QUEX_NAME(Converter_IConv_delete_self),
                                             (ptrdiff_t (*)(struct QUEX_NAME(Converter_tag)*))0,
                                             (void (*)(struct QUEX_NAME(Converter_tag)*))0) ) {
            QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_CONVERTER);
            return (QUEX_NAME(Converter)*)0;
        }

        return &me->base;
    }

    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_open)(QUEX_NAME(Converter)* alter_ego,
                                    const char*           FromCodec, 
                                    const char*           ToCodec)
    {
        QUEX_NAME(Converter_IConv)* me = (QUEX_NAME(Converter_IConv)*)alter_ego;
#       if   defined(__QUEX_OPTION_LITTLE_ENDIAN)
        const bool little_endian_f = true;
#       elif defined(__QUEX_OPTION_BIG_ENDIAN)
        const bool little_endian_f = false;
#       elif defined(__QUEX_OPTION_SYSTEM_ENDIAN) 
        const bool little_endian_f = QUEXED(system_is_little_endian)();
#       endif


        /* Setup conversion handle */
        if( ! ToCodec ) {
            switch( sizeof(QUEX_TYPE_CHARACTER) ) {
            case 4:  ToCodec = little_endian_f ? "UCS-4LE" : "UCS-4BE"; break;
            case 2:  ToCodec = little_endian_f ? "UCS-2LE" : "UCS-2BE"; break;
            case 1:  ToCodec = "ASCII"; break;
            default:  __quex_assert(false); return false;
            }
        } 
        me->handle = iconv_open(ToCodec, FromCodec);
        if( me->handle == (iconv_t)-1 ) return false;
        
        /* ByteN / Character:
         * IConv does not provide something like 'isFixedWidth()'. So, the 
         * safe assumption "byte_n/character != const" is made, except for some
         * well-known examples.                                              */
        me->base.byte_n_per_character = -1;
        if(    __QUEX_STD_strcmp(FromCodec, "UCS-4LE") == 0 
            || __QUEX_STD_strcmp(FromCodec, "UCS-4BE")  == 0) {
            me->base.byte_n_per_character = 4;
        }
        else if(   __QUEX_STD_strcmp(FromCodec, "UCS-2LE") == 0 
                || __QUEX_STD_strcmp(FromCodec, "UCS-2BE")  == 0) {
            me->base.byte_n_per_character = 2;
        }

        return true;
    }

    QUEX_INLINE bool 
    QUEX_NAME(Converter_IConv_convert)(QUEX_NAME(Converter)*  alter_ego, 
                                       uint8_t**              source, const uint8_t*              SourceEnd,
                                       QUEX_TYPE_CHARACTER**  drain,  const QUEX_TYPE_CHARACTER*  DrainEnd)
    /* RETURNS:  true  --> User buffer is filled as much as possible with 
     *                     converted characters.
     *           false --> More raw bytes are needed to fill the user buffer.           
     *
     *  IF YOU GET A COMPILE ERROR HERE, THEN PLEASE HAVE A LOOK AT THE FILE:
     *
     *      quex/code_base/compatibility/iconv-argument-types.h
     * 
     *  'iconv' is defined on different systems with different
     *  types of the second argument. There are two variants 'const char**'
     *  and 'char **'.  If you get an error here, consider defining 
     *
     *            -DQUEX_SETTING_ICONV_2ND_ARG_CONST_CHARPP
     *
     *  as a compile option. If you know of an elegant solution to solve the 
     *  problem for plain 'C', then please, let me know 
     *  <fschaef@users.sourceforge.net>.                                     */
    {
        QUEX_NAME(Converter_IConv)* me                  = (QUEX_NAME(Converter_IConv)*)alter_ego;
        size_t                      source_bytes_left_n = (size_t)(SourceEnd - *source);
        size_t                      drain_bytes_left_n  = (size_t)(DrainEnd - *drain)*sizeof(QUEX_TYPE_CHARACTER);
        size_t                      report;
        
        /* Avoid strange error reports from 'iconv' in case that the source 
         * buffer is empty.                                                  */
        report = iconv(me->handle, 
                       __QUEX_ADAPTER_ICONV_2ND_ARG(source), &source_bytes_left_n,
                       (char**)drain,                        &drain_bytes_left_n);

        if( report != (size_t)-1 ) { 
            /* No Error => Raw buffer COMPLETELY converted.                  */
            __quex_assert(! source_bytes_left_n);
            return drain_bytes_left_n ? false : true;
        }

        switch( errno ) {
        default:
            QUEX_ERROR_EXIT("Unexpected setting of 'errno' after call to GNU's iconv().");

        case EILSEQ:
            QUEX_ERROR_EXIT("Invalid byte sequence encountered for given character coding.");

        case EINVAL:
            /* Incomplete byte sequence for character conversion.
             * => '*source' points to the beginning of the incomplete sequence.
             * => If drain is not filled, then new source content must be 
             *    provided.                                                  */
            return *drain == DrainEnd ? true : false;

        case E2BIG:
            /* The input buffer was not able to hold the number of converted 
             * characters. => Drain is filled to the limit.                 */
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


#endif /*  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__ICONV__CONVERTER_ICONV_I */
