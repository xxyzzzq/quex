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
#   error "__QUEX_FROM must be defined!"
#elif ! defined(__QUEX_FROM_TYPE)
#   error "__QUEX_FROM_TYPE must be defined!"
#elif   defined(__QUEX_TO_TYPE) 
#   error "__QUEX_TO_TYPE must NOT be defined!"
#elif   defined(__QUEX_TO) 
#   error "__QUEX_TO must NOT be defined!"
#elif   defined(__QUEX_TO_CODEC)
#   error "__QUEX_TO_CODEC must NOT be defined!"
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
__QUEX_CONVERTER_STRING(__QUEX_FROM, char)(const __QUEX_FROM_TYPE**  source_pp, 
                                           const __QUEX_FROM_TYPE*   SourceEnd, 
                                           char**                    drain_pp,  
                                           const char*               DrainEnd)
{
    switch( sizeof(char) )
    {
    case 1:
        __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(source_pp,           SourceEnd, 
                                                   (uint8_t**)drain_pp, (const uint8_t*)DrainEnd);
        break;
    case 2:
        __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(source_pp,            SourceEnd, 
                                                    (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
        break;
    case 4:
        __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(source_pp,            SourceEnd, 
                                                    (uint32_t**)drain_pp, (const uint32_t*)DrainEnd);
        break;
    default:
        /* Cannot be handled */
        __quex_assert(false);
}

#   if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE void
    __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(const __QUEX_FROM_TYPE**  source_pp, 
                                                  const __QUEX_FROM_TYPE*   SourceEnd, 
                                                  wchar_t**                 drain_pp,  
                                                  const wchar_t*            DrainEnd)
    {
        switch( sizeof(wchar_t) )
        {
        case 1:
            __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(source_pp,           SourceEnd, 
                                                       (uint8_t**)drain_pp, (const uint8_t*)DrainEnd);
            break;
        case 2:
            __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(source_pp,            SourceEnd, 
                                                        (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
            break;
        case 4:
            __quex_assert(sizeof(char) == 4);
            __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(source_pp,            SourceEnd, 
                                                        (uint32_t**)drain_pp, (const uint32_t*)DrainEnd);
            break;
        default:
            __quex_assert(false); /* Cannot be handled */
        }
    }
#   endif

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<char>
__QUEX_CONVERTER_STRING(__QUEX_FROM, char)(const std::basic_string<__QUEX_FROM_TYPE>& Source)
{
    switch( sizeof(char) )
    {
    case 1:
        std::basic_string<uint8_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(Source); 
        break;
    case 2:
        std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(Source); 
        break;
    case 4:
        std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(Source); 
        break;
    default:
        __quex_assert(false); /* Cannot be handled */
    }

    return std::basic_string<char>((char*)tmp.c_str());
}
#   if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE std::basic_string<wchar_t>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(const std::basic_string<__QUEX_FROM_TYPE>& Source)
    {
        switch( sizeof(wchar_t) )
        {
        case 1:
            std::basic_string<uint8_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(Source); 
            break;
        case 2:
            std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(Source); 
            break;
        case 4:
            std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(Source); 
            break;
        default:
            __quex_assert(false); /* Cannot be handled */
        }

        return std::basic_string<wchar_t>((wchar_t*)tmp.c_str());
    }
#   endif
#endif

#undef __QUEX_TO_TYPE
#undef __QUEX_TO_CODEC
