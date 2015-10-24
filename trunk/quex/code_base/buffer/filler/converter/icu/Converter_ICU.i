/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__CONVERTER_ICU_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__CONVERTER_ICU_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/filler/converter/icu/Converter_ICU>

#if ! defined(QUEX_OPTION_CONVERTER_ICU)
#    error "This header has been included without setting the compile option QUEX_OPTION_CONVERTER_ICU. This could cause problems on systems where the correspondent headers are not installed. Make the inclusion of this header dependent on the above compile option."
#endif

#include <quex/code_base/analyzer/configuration/validation>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE bool
QUEX_NAME(Converter_ICU_open)(QUEX_NAME(Converter)* me, 
                              const char*           FromCoding, 
                              const char*           ToCoding);
QUEX_INLINE bool
QUEX_NAME(Converter_ICU_convert)(QUEX_NAME(Converter)*       me, 
                                 uint8_t**                   source, 
                                 const uint8_t*              SourceEnd, 
                                 QUEX_TYPE_CHARACTER**       drain,  
                                 const QUEX_TYPE_CHARACTER*  DrainEnd);
QUEX_INLINE void
QUEX_NAME(Converter_ICU_delete_self)(QUEX_NAME(Converter)* me);

QUEX_INLINE ptrdiff_t 
QUEX_NAME(Converter_ICU_stomach_byte_n)(QUEX_NAME(Converter)* me);

QUEX_INLINE void 
QUEX_NAME(Converter_ICU_stomach_clear)(QUEX_NAME(Converter)* me);

QUEX_INLINE QUEX_NAME(Converter)*
QUEX_NAME(Converter_ICU_new)(const char* FromCoding, const char* ToCoding)
{
    QUEX_NAME(Converter_ICU)*  me = \
         (QUEX_NAME(Converter_ICU)*)QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(Converter_ICU)),
                                                                   E_MemoryObjectType_CONVERTER);

    me->to_handle   = 0x0;
    me->from_handle = 0x0;
    me->status      = U_ZERO_ERROR;
    /* Setup the pivot buffer                                            */
    me->pivot.source = &me->pivot.buffer[0];
    me->pivot.target = &me->pivot.buffer[0];
    me->reset_upon_next_conversion_f = TRUE;

    if( ! QUEX_NAME(Converter_construct)(&me->base,
                                         FromCoding, ToCoding,
                                         QUEX_NAME(Converter_ICU_open),
                                         QUEX_NAME(Converter_ICU_convert),
                                         QUEX_NAME(Converter_ICU_delete_self),
                                         QUEX_NAME(Converter_ICU_stomach_byte_n),
                                         QUEX_NAME(Converter_ICU_stomach_clear)) ) {
        QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_CONVERTER);
        return (QUEX_NAME(Converter)*)0;
    }

    return &me->base;
}

QUEX_INLINE bool
QUEX_NAME(Converter_ICU_open)(QUEX_NAME(Converter)* alter_ego, 
                              const char*           FromCoding, 
                              const char*           ToCoding)
{
    QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;
#       if   defined(__QUEX_OPTION_LITTLE_ENDIAN)
    const bool little_endian_f = true;
#       elif defined(__QUEX_OPTION_BIG_ENDIAN)
    const bool little_endian_f = false;
#       elif defined(__QUEX_OPTION_SYSTEM_ENDIAN) 
    const bool little_endian_f = QUEXED(system_is_little_endian)();
#       endif

    __quex_assert(me);

    /* Default: assume input encoding to have dynamic character sizes.   */
    if( ucnv_compareNames(FromCoding, "UTF32") == 0 ) {
        FromCoding = "UTF32_PlatformEndian";
    }
    else if( ucnv_compareNames(FromCoding, "UTF16") == 0 ) {
        FromCoding = "UTF16_PlatformEndian";
    }

    /* Open conversion handles                                           */
    me->status = U_ZERO_ERROR;
    me->from_handle = ucnv_open(FromCoding, &me->status);
    if( me->from_handle == NULL || ! U_SUCCESS(me->status) ) return false;

    if( ! U_SUCCESS(me->status) ) {
        return false;
    }

    /* ByteN / Character:                                               */
    if( ucnv_isFixedWidth(me->from_handle, &me->status) && U_SUCCESS(me->status) ) {
        me->base.byte_n_per_character = ucnv_getMaxCharSize(me->from_handle);
    }
    else {
        me->base.byte_n_per_character = -1;
    }

    if( ! ToCoding ) {
         /* From the ICU Documentation: "ICU does not use UCS-2. UCS-2 is a
          * subset of UTF-16. UCS-2 does not support surrogates, and UTF-16
          * does support surrogates. This means that UCS-2 only supports
          * UTF-16's Base Multilingual Plane (BMP). The notion of UCS-2 is
          * deprecated and dead. Unicode 2.0 in 1996 changed its default
          * encoding to UTF-16." (userguide.icu-project.org/icufaq)      */
        switch( sizeof(QUEX_TYPE_CHARACTER) ) {
        case 4:  ToCoding = little_endian_f ? "UTF32-LE" : "UTF32-LE"; break;
        case 2:  ToCoding = little_endian_f ? "UTF16-LE" : "UTF16-LE"; break;
        case 1:  ToCoding = "ISO-8859-1"; break;
        default:  __quex_assert(false); return false;
        }
    } 

    me->status = U_ZERO_ERROR;
    me->to_handle = ucnv_open(ToCoding, &me->status);
    if( me->to_handle == NULL || ! U_SUCCESS(me->status) ) return false;

    /* Setup the pivot buffer                                            */
    //me->pivot.source = &me->pivot.buffer[0];
    //me->pivot.target = &me->pivot.buffer[0];         
    me->reset_upon_next_conversion_f = TRUE;

    return true;
}

QUEX_INLINE bool
QUEX_NAME(Converter_ICU_convert)(QUEX_NAME(Converter)*       alter_ego, 
                                 uint8_t**                   source, 
                                 const uint8_t*              SourceEnd, 
                                 QUEX_TYPE_CHARACTER**       drain,  
                                 const QUEX_TYPE_CHARACTER*  DrainEnd)
/* RETURNS: 'true'  if the drain was completely filled.
 *          'false' if the drain could not be filled completely and 
 *                  more source bytes are required.                      */
{
    QUEX_NAME(Converter_ICU)* me          = (QUEX_NAME(Converter_ICU)*)alter_ego;
    uint8_t*                  SourceBegin = *source;
    (void)SourceBegin;
#   if 0
    QUEX_TYPE_CHARACTER*      DEBUG_DrainBegin  = *drain;
    int                       i = 0;
#   endif

    __quex_assert(me);
    __quex_assert(me->to_handle);
    __quex_assert(me->from_handle);
    __quex_assert(SourceEnd >= *source);
    __quex_assert(DrainEnd >= *drain);
    __quex_assert(&me->pivot.buffer[0] <= me->pivot.source);
    __quex_assert(me->pivot.source     <= me->pivot.target);
    __quex_assert(me->pivot.target     <= &me->pivot.buffer[QUEX_SETTING_ICU_PIVOT_BUFFER_SIZE]);

    me->status = U_ZERO_ERROR;

#   if 0
    {
        printf("#source:          [");
        for(i=0; i<(SourceEnd  - SourceBegin); ++i) {
            printf("%02X.", (int)SourceBegin[i]);
        }
        printf("]\n");
        printf("#reset_f: %s;\n", me->reset_upon_next_conversion_f ? "TRUE" : "FALSE");
    }
#   endif
    ucnv_convertEx(me->to_handle, me->from_handle,
                   (char**)drain,        (const char*)DrainEnd,
                   (const char**)source, (const char*)SourceEnd,
                   &me->pivot.buffer[0], &me->pivot.source, &me->pivot.target, &me->pivot.buffer[QUEX_SETTING_ICU_PIVOT_BUFFER_SIZE],
                   /* reset = */me->reset_upon_next_conversion_f ? TRUE : FALSE, 
                   /* flush = */FALSE,
                   &me->status);
    me->reset_upon_next_conversion_f = FALSE;

    me->status = U_ZERO_ERROR;
#   if 0
    {
        printf("#pending to:source:   %i;\n", (int)ucnv_toUCountPending(me->from_handle, &me->status));
        printf("#pending from:source: %i;\n", (int)ucnv_fromUCountPending(me->from_handle, &me->status));
        printf("#pending to:drain:    %i;\n", (int)ucnv_toUCountPending(me->to_handle, &me->status));
        printf("#pending from:drain:  %i;\n", (int)ucnv_fromUCountPending(me->to_handle, &me->status));
        printf("#status:          %i;\n", me->status);
        me->status = U_ZERO_ERROR;
        printf("#pending from:    %i;\n", (int)ucnv_toUCountPending(me->from_handle, &me->status));
        me->status = U_ZERO_ERROR;
        printf("#pending to:      %i;\n", (int)ucnv_toUCountPending(me->to_handle, &me->status));
        printf("#source consumed: %i/%i; p.source: @%i; p.target @%i;\n",
               (int)(*source - SourceBegin), (int)(SourceEnd - SourceBegin),
               (int)(me->pivot.source - &me->pivot.buffer[0]), 
               (int)(me->pivot.target - &me->pivot.buffer[0])); 
        printf("#consumed source: [");
        for(i=0; i<(*source  - SourceBegin); ++i) {
            printf("%02X.", (int)SourceBegin[i]);
        }
#   endif
#   if 0
        printf("]\n");
        printf("#pivot:           [");
        for(i=0; i<8; ++i) {
            if( me->pivot.source - &me->pivot.buffer[0] == i ) printf("s!");
            if( me->pivot.target - &me->pivot.buffer[0] == i ) printf("t!");
            printf("%02X.", (int)me->pivot.buffer[i]);
        }
#   endif
#   if 0
        printf("]\n");
        printf("#drain:           [");
        for(i=0; i<(*drain  - DEBUG_DrainBegin); ++i) {
            printf("%02X.", (int)DEBUG_DrainBegin[i]);
        }
        printf("]\n");
    }
#   endif
    // *source -= ucnv_toUCountPending(me->from_handle, &me->status);
    // *source -= ucnv_fromUCountPending(me->to_handle, &me->status);
    __quex_assert(*source >= SourceBegin);

    return *drain == DrainEnd ? true : false;
}

QUEX_INLINE ptrdiff_t 
QUEX_NAME(Converter_ICU_stomach_byte_n)(QUEX_NAME(Converter)* alter_ego)
/* To compute the source bytes which have not been converted during the last
 * conversion the 3-buffer setup must be considered. First, ICU converts the
 * source data into a pivot buffer encoded in UTF16. The the content of the
 * pivot buffer is converted into the user's drain. 
 * 
 *  source buffer  [x.x.x|y.y|z|a.a.a|b.b.b|c.c. ]    'c's are not complete
 *  (e.g. UTF8)    :   .-'   : '---. '-.   '---.      => pending = 2
 *                 :   :     '-.   :   '---.   :      
 *  pivot buffer   [X.X|Y.Y|Y.Y|Z.Z|A.A|A.A|B.B| ...  pivot.source--> 'A's
 *  (fix UTF16)    :   :   .---'   :                  pivot.target--> after 'B's
 *                 :   :   :   .---'                  
 *  drain buffer   [ X | Y | Z ]                      Drain filled to limit
 *  (some UCS)                                        'A' and 'B' cannot be 
 *                                                    converted.
 * 
 * => Source bytes NOT translated in the last conversion:
 * 
 *    (1) The 'c's that where incomplete: 'ucnv_toUCountPending()'
 *    (2) Source bytes that produced the 'A's and 'B's in the pivot buffer.  
 *
 * However, what if the conversion contained a 0xFFFD, i.e. a conversion error.
 * At the current time, I know of no reliable way to get the stomach byte
 * number <fschaef 2015y10m24d>
 * => Only report, if nothing left in pivot buffer.                          */
{
    QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

    if( me->pivot.source != me->pivot.target ) {
        return (ptrdiff_t)-1;                      /* Unable to tell. Sorry. */
    }
    return ucnv_toUCountPending(me->from_handle, &me->status);
}

QUEX_INLINE void 
QUEX_NAME(Converter_ICU_stomach_clear)(QUEX_NAME(Converter)* alter_ego)
{
    QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

    // if( me->from_handle ) ucnv_reset(me->from_handle);
    //  if( me->to_handle )   ucnv_reset(me->to_handle);

    /* Reset the pivot buffer iterators */
    //me->pivot.source = &me->pivot.buffer[0];
    //me->pivot.target = &me->pivot.buffer[0];
    me->reset_upon_next_conversion_f = TRUE;

    me->status = U_ZERO_ERROR;
}

QUEX_INLINE void
QUEX_NAME(Converter_ICU_delete_self)(QUEX_NAME(Converter)* alter_ego)
{
    QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

    ucnv_close(me->from_handle);
    ucnv_close(me->to_handle);

    QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_CONVERTER);

    /* There should be a way to call 'ucnv_flushCache()' as soon as all converters
     * are freed automatically.                                                       */
    u_cleanup();
}

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICU_I__ */
