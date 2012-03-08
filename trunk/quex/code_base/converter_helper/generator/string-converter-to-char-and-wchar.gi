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
 * be defined before the inclusion of this file.
 *
 * This generator is a special case of what is implemented in 'string-converter.gi'.
 *
 * (C) 2010-2012 Frank-Rene Schaefer 
 * ABSOLUTELY NO WARRANTY                                                    */
#if __QUEX_TO != char && __QUEX_TO != wchar_t
#   error "This generator has been designed soley for generating conversions to char or wchar_t."
#endif

#if ! defined(__QUEX_DRAIN_CODEC)
#   error "__QUEX_DRAIN_CODEC must be defined."
#elif __QUEX_DRAIN_CODEC == 8 
    /* OK */
#elif __QUEX_DRAIN_CODEC == 16 
    /* OK */
#elif __QUEX_DRAIN_CODEC == 32
    /* OK */
#else
#   error "Codec of 'char' or 'wchar' must be either 'UTF8', 'UTF16' or 'UTF32' -> 8, 16, or 32. Define QUEX_SETTING_CHAR_CODEC and QUEX_SETTING_WCHAR_CODEC."

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_G_SOURCE_TYPE**  source_pp, 
                                                const __QUEX_G_SOURCE_TYPE*   SourceEnd, 
                                                __QUEX_TYPE_DRAIN**           drain_pp,  
                                                const __QUEX_TYPE_DRAIN*      DrainEnd)
{
#   if   __QUEX_DRAIN_CODEC == 8
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 1);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(source_pp,           SourceEnd, 
                                               (uint8_t**)drain_pp, (const uint8_t*)DrainEnd);
#   elif __QUEX_DRAIN_CODEC == 16
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 2);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(source_pp,            SourceEnd, 
                                                (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
#   elif __QUEX_DRAIN_CODEC == 32
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 4);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(source_pp,            SourceEnd, 
                                                (uint32_t**)drain_pp, (const uint32_t*)DrainEnd);
#   endif
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_G_SOURCE_TYPE>& Source)
{
#   if   __QUEX_DRAIN_CODEC == 8
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 1);
    std::basic_string<uint8_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(Source);

#   elif __QUEX_DRAIN_CODEC == 16
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 2);
    std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(Source);

#   elif __QUEX_DRAIN_CODEC == 32
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 4);
    std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(Source);

#   endif

    return std::basic_string<__QUEX_TYPE_DRAIN>((__QUEX_TYPE_DRAIN*)tmp.c_str());
}
#endif

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_DRAIN_CODEC
