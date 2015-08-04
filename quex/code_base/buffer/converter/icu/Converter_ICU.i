/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__CONVERTER_ICU_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__ICU__CONVERTER_ICU_I

#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/converter/icu/Converter_ICU>

#if ! defined(QUEX_OPTION_CONVERTER_ICU)
#    error "This header has been included without setting the compile option QUEX_OPTION_CONVERTER_ICU. This could cause problems on systems where the correspondent headers are not installed. Make the inclusion of this header dependent on the above compile option."
#endif

#include <quex/code_base/analyzer/configuration/validation>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void
    QUEX_NAME(Converter_ICU_open)(QUEX_NAME(Converter)* me, 
                                  const char*           FromCodingName, 
                                  const char*           ToCodingName);
    QUEX_INLINE bool
    QUEX_NAME(Converter_ICU_convert)(QUEX_NAME(Converter)*       me, 
                                     uint8_t**                   source, 
                                     const uint8_t*              SourceEnd, 
                                     QUEX_TYPE_CHARACTER**       drain,  
                                     const QUEX_TYPE_CHARACTER*  DrainEnd);
    QUEX_INLINE void
    QUEX_NAME(Converter_ICU_delete_self)(QUEX_NAME(Converter)* me);

    QUEX_INLINE void 
    QUEX_NAME(Converter_ICU_on_conversion_discontinuity)(QUEX_NAME(Converter)* me);

    QUEX_INLINE QUEX_NAME(Converter)*
    QUEX_NAME(Converter_ICU_new)()
    {
        QUEX_NAME(Converter_ICU)*  me = \
             (QUEX_NAME(Converter_ICU)*)QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(Converter_ICU)),
                                                                       QUEXED(MemoryObjectType_CONVERTER));

        me->base.open        = QUEX_NAME(Converter_ICU_open);
        me->base.convert     = QUEX_NAME(Converter_ICU_convert);
        me->base.delete_self = QUEX_NAME(Converter_ICU_delete_self);
        me->base.on_conversion_discontinuity = QUEX_NAME(Converter_ICU_on_conversion_discontinuity);

        me->to_handle   = 0x0;
        me->from_handle = 0x0;
        me->status      = U_ZERO_ERROR;

        return &me->base;
    }

    QUEX_INLINE void
    QUEX_NAME(Converter_ICU_open)(QUEX_NAME(Converter)* alter_ego, 
                                  const char*           FromCodingName, 
                                  const char*           ToCodingName)
    {
        QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

        __quex_assert(me);

        /* Default: assume input encoding to have dynamic character sizes.   */
        me->base.dynamic_character_size_f = true;

        /* Open conversion handles                                           */
        me->from_handle = ucnv_open(FromCodingName, &me->status);

        if( ! U_SUCCESS(me->status) ) 
            QUEX_ERROR_EXIT("Input Coding not supported by ICU converter.");

        if( ToCodingName ) {
            me->to_handle = ucnv_open(ToCodingName, &me->status);
        } else {
            switch( sizeof(QUEX_TYPE_CHARACTER) ) {
            case 4:  
                /* Please, use the ICU converter utility to find correct ICU 
                 * coding names:
                 * http://demo.icu-project.org/icu-bin/convexp?s=IANA        */
#               if   defined(__QUEX_OPTION_SYSTEM_ENDIAN)
                me->to_handle = ucnv_open("UTF32", &me->status); 
#               elif defined(__QUEX_OPTION_LITTLE_ENDIAN)
                me->to_handle = ucnv_open("UTF32-LE", &me->status); 
#               elif defined(__QUEX_OPTION_BIG_ENDIAN)
                me->to_handle = ucnv_open("UTF32-BE", &me->status); 
#               endif
                break;
            case 2:  
                /* Currently no concept exists to handle this case. See 
                 * feature request 2749855                                   */
#               if   defined(__QUEX_OPTION_SYSTEM_ENDIAN)
                /* 2 byte encoding may use the 'direct converter for UChar'  */
                me->to_handle = ucnv_open("UTF16", &me->status); 
#               elif defined(__QUEX_OPTION_LITTLE_ENDIAN)
                me->to_handle = ucnv_open("UTF16-LE", &me->status); 
#               elif defined(__QUEX_OPTION_BIG_ENDIAN)
                me->to_handle = ucnv_open("UTF16-BE", &me->status); 
#               endif
                break;
            case 1:  
                me->to_handle = ucnv_open("ISO-8859-1", &me->status); 
                break;
            default:
                QUEX_ERROR_EXIT("ICU character conversion: target coding different from unicode not yet supported.");
            }
        }

        /* Setup the pivot buffer */
        me->pivot_iterator_begin = me->pivot_buffer;
        me->pivot_iterator_end   = me->pivot_buffer;
    }

    QUEX_INLINE bool
    QUEX_NAME(Converter_ICU_convert)(QUEX_NAME(Converter)* alter_ego, 
                                     uint8_t**             source, const uint8_t*              SourceEnd, 
                                     QUEX_TYPE_CHARACTER** drain,  const QUEX_TYPE_CHARACTER*  DrainEnd)
    {
        QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;
        /* RETURNS: 'true'  if the drain was completely filled.
         *          'false' if the drain could not be filled completely and 
         *                  more source bytes are required.                  */
        __quex_assert(me);
        __quex_assert(SourceEnd >= *source);
        __quex_assert(DrainEnd >= *drain);
        __quex_assert(me->handle);

        me->status = U_ZERO_ERROR;

        ucnv_convertEx(me->to_handle, me->from_handle,
                       (char**)drain,        (const char*)DrainEnd,
                       (const char**)source, (const char*)SourceEnd,
                       me->pivot_buffer, 
                       &me->pivot_iterator_begin, &me->pivot_iterator_end, 
                       me->pivot_buffer + QUEX_SETTING_ICU_PIVOT_BUFFER_SIZE,
                       /* reset = */FALSE, 
                       /* flush = */FALSE,
                       &me->status);

        return *drain == DrainEnd ? true : false;

        /*
        if( me->status == U_BUFFER_OVERFLOW_ERROR) {
            return false;
        }
        else {
            if( ! U_SUCCESS(me->status) ) {
                QUEX_ERROR_EXIT(u_errorName(me->status));
            }
            / * Are more source bytes needed to fill the drain buffer? If so we return 'false' * /
            if( *drain != DrainEnd && *source == SourceEnd ) return false;
            else                                             return true;
        }
        */
    }

    QUEX_INLINE void 
    QUEX_NAME(Converter_ICU_on_conversion_discontinuity)(QUEX_NAME(Converter)* alter_ego)
    {
        QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

        ucnv_reset(me->from_handle);
        if( me->to_handle != 0x0 ) ucnv_reset(me->to_handle);

        /* Reset the pivot buffer iterators */
        me->pivot_iterator_begin = me->pivot_buffer;
        me->pivot_iterator_end   = me->pivot_buffer;

        me->status = U_ZERO_ERROR;
    }

    QUEX_INLINE void
    QUEX_NAME(Converter_ICU_delete_self)(QUEX_NAME(Converter)* alter_ego)
    {
        QUEX_NAME(Converter_ICU)* me = (QUEX_NAME(Converter_ICU)*)alter_ego;

        ucnv_close(me->from_handle);
        ucnv_close(me->to_handle);

        QUEXED(MemoryManager_free)((void*)me, QUEXED(MemoryObjectType_CONVERTER));

        /* There should be a way to call 'ucnv_flushCache()' as soon as all converters
         * are freed automatically.                                                       */
        u_cleanup();
    }

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICU_I__ */
