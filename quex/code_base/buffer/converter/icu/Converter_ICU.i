/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICU_I__
#define __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICU_I__

#include <quex/code_base/compatibility/inttypes.h>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE void
    QuexConverter_ICU_open(QuexConverter* alter_ego, 
                           const char* FromCodingName, const char* ToCodingName)
    {
        QuexConverter_ICU* me = (QuexConverter_ICU*)alter_ego;
        __quex_assert(me != 0x0);

        me->from_handle = ucnv_open(FromCodingName, &me->status);

        if( ! U_SUCCESS(me->status) ) 
            QUEX_ERROR_EXIT("Input Coding not supported by ICU converter.");

        if( ToCodingName != 0x0 ) {
            me->to_handle = ucnv_open(ToCodingName, &me->status);
        } else {
            switch( sizeof(QUEX_CHARACTER_TYPE) ) {
            case 4:  
                me->to_handle = ucnv_open("UTF32_PlatformEndian", &me->status);  /* UCS-4 */
                break;
            case 2:  
                me->to_handle = 0x0; /* 2 byte encoding may use the 'direct converter for UChar' */
                break;
            case 1:  
                me->to_handle = ucnv_open("ISO-8859-1", &me->status);            /* ASCII */
                break;
            default:
                QUEX_ERROR_EXIT("ICU character conversion: target coding different from unicode not yet supported.");
            }
        }

    }

    QUEX_INLINE bool
    QuexConverter_ICU_convert(QuexConverter*        alter_ego, 
                              uint8_t**             source, const uint8_t*              SourceEnd, 
                              QUEX_CHARACTER_TYPE** drain,  const QUEX_CHARACTER_TYPE*  DrainEnd)
    {
        QuexConverter_ICU*    me         = (QuexConverter_ICU*)alter_ego;
        const size_t          SourceSize = SourceEnd - *source;
        const size_t          DrainSize  = DrainEnd  - *drain;

        __quex_assert(me != 0x0);
        me->status = U_ZERO_ERROR;

        if( me->to_handle == 0x0 ) {
            /* Convert according to QUEX_CHARACTER_TYPE */
            if( sizeof(QUEX_CHARACTER_TYPE) == sizeof(UChar) )              /* 16 bit */
                /* NOTE: 'UChar' is defined to be wchar_t, if sizeof(wchar_t) == 2 byte, 
                 *       otherwise it as defined as uint16_t.                        
                 * We need to cast to UChar, since otherwise the code would not compile for sizeof() != 2.
                 * Nevertheless, in this case the code would never be executed.                            */
                ucnv_toUChars(me->from_handle, 
                              (UChar*)*drain,  (int32_t)DrainSize,
                              (const char*)&source, (int32_t)SourceSize, 
                              &me->status);

            else 
                QUEX_ERROR_EXIT("ICU: QUEX_CHARACTER_TYPE different from 16bit, while the 'to-converter' is undefined.");
            *drain  += 1;
            *source += 1;
        } else {
            ucnv_convertEx(me->from_handle, me->to_handle,
                           (char**)drain, (const char*)DrainEnd,
                           (const char**)source, (const char*)SourceEnd,
                           NULL, NULL, NULL, NULL,
                           TRUE, TRUE,
                           &me->status);
        }

        if( me->status == U_BUFFER_OVERFLOW_ERROR) {
            return true;
        }
        else {
            if( ! U_SUCCESS(me->status) ) {
                QUEX_ERROR_EXIT(u_errorName(me->status));
            }
            /* Are more source bytes needed to fill the drain buffer. */
            if( *drain != DrainEnd && *source == SourceEnd ) return true;
            else                                             return false;
        }
    }

    QUEX_INLINE void
    QuexConverter_ICU_delete_self(QuexConverter* alter_ego)
    {
        QuexConverter_ICU* me = (QuexConverter_ICU*)alter_ego;

        ucnv_close(me->from_handle);
        ucnv_close(me->to_handle);

        MemoryManager_QuexConverter_ICU_free(me);
    }

    QUEX_INLINE QuexConverter*
    QuexConverter_ICU_new()
    {
        QuexConverter_ICU*  me = MemoryManager_QuexConverter_ICU_allocate();

        me->base.open        = QuexConverter_ICU_open;
        me->base.convert     = QuexConverter_ICU_convert;
        me->base.delete_self = QuexConverter_ICU_delete_self;

        me->to_handle   = 0x0;
        me->from_handle = 0x0;
        me->status      = U_ZERO_ERROR;

        return (QuexConverter*)me;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
}
#endif


#include <quex/code_base/buffer/BufferFiller.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER__CONVERTER_ICONV_I__ */
