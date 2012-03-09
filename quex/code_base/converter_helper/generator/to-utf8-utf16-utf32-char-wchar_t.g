/* -*- C++ -*- vim: set syntax=cpp: 
 *
 * Declaration of all converter functions towards 'utf8', 'utf16', 'utf32',
 * 'char', and 'wchar_t': 
 *
 *    __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf8)(...)
 *    __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf16)(...)
 *    __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf32)(...)
 *    __QUEX_CONVERTER_CHAR(__QUEX_FROM, char)(...)
 *    __QUEX_CONVERTER_CHAR(__QUEX_FROM, wchar_t)(...)
 *
 *    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(...)     for string and buffer 
 *    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(...)    for string and buffer 
 *    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(...)    for string and buffer 
 *    __QUEX_CONVERTER_STRING(__QUEX_FROM, char)(...)     for string and buffer 
 *    __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(...)  for string and buffer 
 *
 * (C) 2012 Frank-Rene Schaefer, ABSOLUTELY NO WARRANTY                      */
#if   ! defined(__QUEX_FROM)
#   error "__QUEX_FROM must be defined!"
#elif ! defined(__QUEX_FROM_TYPE)
#   error "__QUEX_FROM_TYPE must be defined!"
#endif

/* (1) Character converters */
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(__QUEX_FROM, utf8)(const __QUEX_FROM_TYPE**  input_pp, 
                                         uint8_t**                 output_pp);
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(__QUEX_FROM, utf16)(const __QUEX_FROM_TYPE**  input_pp, 
                                          uint16_t**                output_pp);
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(__QUEX_FROM, utf32)(const __QUEX_FROM_TYPE**  input_pp, 
                                          uint32_t**                output_pp);
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(__QUEX_FROM, char)(const __QUEX_FROM_TYPE**  input_pp, 
                                         char**                    output_pp);
#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(__QUEX_FROM, wchar_t)(const __QUEX_FROM_TYPE**  input_pp, 
                                            wchar_t**                 output_pp);
#endif

/* (2) String converters */
QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(const __QUEX_FROM_TYPE**  source_pp, 
                                           const __QUEX_FROM_TYPE*   SourceEnd, 
                                           uint8_t**                 drain_pp,  
                                           const uint8_t*            DrainEnd);
QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(const __QUEX_FROM_TYPE**  source_pp, 
                                            const __QUEX_FROM_TYPE*   SourceEnd, 
                                            uint16_t**                drain_pp,  
                                            const uint16_t*           DrainEnd);
QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(const __QUEX_FROM_TYPE**  source_pp, 
                                            const __QUEX_FROM_TYPE*   SourceEnd, 
                                            __QUEX_TYPE_DRAIN**       drain_pp,  
                                            const __QUEX_TYPE_DRAIN*  DrainEnd);
QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, char)(const __QUEX_FROM_TYPE**  input_pp, 
                                           char**                    output_pp);
#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(const __QUEX_FROM_TYPE**  input_pp, 
                                              wchar_t**                 output_pp);
#endif

#if ! defined(__QUEX_OPTION_PLAIN_C)
    QUEX_INLINE std::basic_string<uint8_t>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(const std::basic_string<__QUEX_FROM_TYPE>& Source);
    QUEX_INLINE std::basic_string<uint16_t>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(const std::basic_string<__QUEX_FROM_TYPE>& Source);
    QUEX_INLINE std::basic_string<uint32_t>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(const std::basic_string<__QUEX_FROM_TYPE>& Source);
    QUEX_INLINE std::basic_string<char>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, char)(const std::basic_string<__QUEX_FROM_TYPE>& Source);
#   if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE std::basic_string<wchar_t>
    __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(const std::basic_string<__QUEX_FROM_TYPE>& Source);
#   endif
#endif

