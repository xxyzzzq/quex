/* -*- C++ -*- vim: set syntax=cpp: */



typedef struct {
    QuexConverter  base;

    UConverter    *from_handle;
    UConverter    *to_handle;
    UErrorCode     status;

} Quex_ICU_Converter;


QUEX_INLINE void
__QuexBufferFiller_ICU_open(QuexConverter* alter_ego, 
                            const char* FromCodingName, const char* ToCodingName)
{
    Quex_ICU_Converter* me = (Quex_ICU_Converter*)alter_ego;
    __quex_assert(me != 0x0);
        QUEX_ERROR_EXIT("Currently only conversion to internal unicode is supported for ICU.");

    me->handle = ucnv_open(FromCodingName, &status);

    if( ! U_SUCCESS(me->handle) ) 
        QUEX_ERROR_EXIT("Input Coding not supported by ICU converter.");

    if( ToCodingName == 0x0 ) {
        me->to_handle = 0x0;
    } else {
        QUEX_ERROR_EXIT("ICU character conversion: target coding different from unicode not yet supported.");
        /*
            me->to_handle = ucnv_open(ToCodingName, &status);
            if( ! U_SUCCESS(me->handle) ) 
                QUEX_ERROR_EXIT("Input Coding not supported by ICU converter.");
        */
    }

}

QUEX_INLINE bool
__QuexBufferFiller_ICU_convert(QuexConverter*        alter_ego, 
                               void**                source, size_t SourceSize, 
                               QUEX_CHARACTER_TYPE** drain,  size_t DrainSize)
{
    void*                 SourceEnd = *source + SourceSize;
    QUEX_CHARACTER_TYPE*  DrainEnd  = *drain  + DrainSize;
    Quex_ICU_Converter*   me        = (Quex_ICU_Converter*)alter_ego;
    __quex_assert(me != 0x0);

    if( me->to_handle == 0x0 ) {
    /* Convert according to QUEX_CHARACTER_TYPE */
#   if   sizeof(QUEX_CHARACTER_TYPE) == sizeof(uint32_t)             /* 32 bit */
        ucnv_toUnicode(me->handle, 
                       drain, DrainEnd
                       source, SourceSize, 
                       NULL, TRUE, &status);

#   elif sizeof(QUEX_CHARACTER_TYPE) == sizeof(UChar)               /* 16 bit */
        /* NOTE: 'UChar' is defined to be wchar_t, if sizeof(wchar_t) == 2 byte, 
         *       otherwise it as defined as uint16_t.                         */
        ucnv_toUChars(me->handle, 
                      drain, DrainEnd
                      source, SourceSize, 
                      NULL, TRUE, &status);
#   elif sizeof(QUEX_CHARACTER_TYPE) == 1                          /* 8 bit   */
#   else
        QUEX_ERROR_EXIT("QUEX_CHARACTER_TYPE defines a type of unsupported size (i.e. not 8, 16, or 32 bit).");
#   endif
    } else {
        QUEX_ERROR_EXIT("ICU character conversion: target coding different from unicode not yet supported.");
    }

    if(status == U_BUFFER_OVERFLOW_ERROR) {
        return true;
    }
    else {
        assert(U_SUCCESS(status));
        /* Are more source bytes needed to fill the drain buffer. */
        if( *drain != DrainEnd && *source == SourceEnd ) return true;
        else                                           return false;
    }
}

QUEX_INLINE void
__QuexBufferFiller_ICU_close(QuexConverter* alter_ego, const char* FromCodingName)
{
    Quex_ICU_Converter* me = (Quex_ICU_Converter*)alter_ego;

    ucnv_close(me->handle);
}

QUEX_INLINE void
QuexBufferFiller_ICU_converter_init(QuexConverter* alter_ego)
{
    Quex_ICU_Converter* me = (Quex_ICU_Converter*)alter_ego;

    QuexBufferFiller_converter_init(alter_ego, 
                                    __QuexBufferFiller_ICU_open,
                                    __QuexBufferFiller_ICU_convert,
                                    __QuexBufferFiller_ICU_close);
    me->handle = 0x0;
    me->status = U_ZERO_ERROR;
}
