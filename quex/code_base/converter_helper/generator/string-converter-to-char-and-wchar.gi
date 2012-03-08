/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Generate string converter functions which convert a string from one 
 * character codec into 'char' or 'wchar'. The conversion is implemented by means
 * of a character converter function given by:
 *
 *            __QUEX_CONVERTER_CHAR(FROM, TO)(in, out); 
 *
 * which converts only a single character. The converter function must
 * be defined before the inclusion of this file. This file implements default
 * converters for char and wchar. So for 'char' utf8 us used for 'wchar' utf16
 * or utf32 are used depending on the system's settings.
 *
 * This generator is a special case of what is implemented in 'string-converter.gi'.
 *
 * (C) 2010-2012 Frank-Rene Schaefer 
 * ABSOLUTELY NO WARRANTY                                                    */

#if   ! defined(__QUEX_FROM)
#   error "__QUEX_FROM must be defined."
#elif ! defined(__QUEX_FROM_TYPE)
#   error "__QUEX_FROM_TYPE must be defined."
#elif ! defined(__QUEX_TO_TYPE)
#   error "__QUEX_TO_TYPE must be defined."
#elif ! defined(__QUEX_TO) || (__QUEX_TO != char && __QUEX_TO != wchar_t)
#   error "__QUEX_TO must be defined as 'char' or 'wchar_t'."
#elif ! defined(__QUEX_TO_CODEC)
#   error "__QUEX_TO_CODEC must be defined."
#elif __QUEX_TO_CODEC == utf8 
    /* OK */
#elif __QUEX_TO_CODEC == utf16 
    /* OK */
#elif __QUEX_TO_CODEC == utf32
    /* OK */
#else
#   error "Codec of 'char' or 'wchar' must be either 'utf8', 'utf16' or 'utf32'. __QUEX_SETTING_CHAR_CODEC or __QUEX_SETTING_WCHAR_CODEC is not propperly defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_FROM_TYPE**  source_pp, 
                                                const __QUEX_FROM_TYPE*   SourceEnd, 
                                                __QUEX_TO_TYPE**          drain_pp,  
                                                const __QUEX_TO_TYPE*     DrainEnd)
{
#   if   __QUEX_TO_CODEC == utf8
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 1);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(source_pp,           SourceEnd, 
                                               (uint8_t**)drain_pp, (const uint8_t*)DrainEnd);
#   elif __QUEX_TO_CODEC == utf16
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 2);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(source_pp,            SourceEnd, 
                                                (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
#   elif __QUEX_TO_CODEC == utf32
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 4);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(source_pp,            SourceEnd, 
                                                (uint32_t**)drain_pp, (const uint32_t*)DrainEnd);
#   endif
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TO_TYPE>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_FROM_TYPE>& Source)
{
#   if   __QUEX_TO_CODEC == 8
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 1);
    std::basic_string<uint8_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(Source);

#   elif __QUEX_TO_CODEC == 16
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 2);
    std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(Source);

#   elif __QUEX_TO_CODEC == 32
    __quex_assert(sizeof(__QUEX_TO_TYPE) == 4);
    std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(Source);

#   endif

    return std::basic_string<__QUEX_TO_TYPE>((__QUEX_TO_TYPE*)tmp.c_str());
}
#endif

#undef __QUEX_TO
#undef __QUEX_TO_TYPE
#undef __QUEX_TO_CODEC
