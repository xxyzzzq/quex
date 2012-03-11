/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Provide the implementation of character and string converter functions
 * FROM the buffer's unicode to utf8, utf16, utf32, char, and wchar_t.
 *
 * STEPS:
 *
 * (1) Include the COMPLETE implementation of a reference transformation.
 *     That is, access one of the following:
 *
 *             "character-converter-from-utf8.i"
 *             "character-converter-from-utf16.i"
 *             "character-converter-from-utf32.i"
 *
 * (2) Map the functions of the pattern
 *
 *        __QUEX_CONVERTER_CHAR(unicode, *)(....)
 *        __QUEX_CONVERTER_STRING(unicode, *)(....)
 *
 *     to what is appropriate from the given headers, e.g.
 *
 *        __QUEX_CONVERTER_CHAR(utf8, *)(....)
 *        __QUEX_CONVERTER_STRING(utf8, *)(....)
 *
 * These functions ARE DEPENDENT on QUEX_TYPE_CHARACTER.
 * => Thus, they are placed in the analyzer's namespace.
 *
 * 2010 (C) Frank-Rene Schaefer; 
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I

#include <quex/code_base/definitions>
#include <quex/code_base/asserts>

/* (1) Access the implementation of the converter that will implement
 *     the unicode conversion.                                               */
#if   QUEX_SETTING_CHARACTER_SIZE == 1
#    include <quex/code_base/converter_helper/from-utf8.i>
#    define __QUEX_FROM       utf8
#    define __QUEX_FROM_TYPE  uint8_t
#elif QUEX_SETTING_CHARACTER_SIZE == 2
#    include <quex/code_base/converter_helper/from-utf16.i>
#    define __QUEX_FROM       utf16
#    define __QUEX_FROM_TYPE  uint16_t
#elif QUEX_SETTING_CHARACTER_SIZE == 4
#    include <quex/code_base/converter_helper/from-utf32.i>
#    define __QUEX_FROM       utf32
#    define __QUEX_FROM_TYPE  uint32_t
#else
#    error "Unfortunately, no character converter can be provided for the buffer's codec."
#endif

QUEX_NAMESPACE_MAIN_OPEN

/* (2) Route the converters from 'buffer' to the implementing converter. */
QUEX_INLINE void
__QUEX_CONVERTER_CHAR(buffer, utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                    uint8_t**                    output_pp)
{ __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf8)((const __QUEX_TYPE_FROM**)input_pp, output_pp); }

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(buffer, utf16)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                     uint16_t**                   output_pp);
{ __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf16)((const __QUEX_TYPE_FROM**)input_pp, output_pp); }

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(buffer, utf32)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                     uint32_t**                   output_pp)
{ __QUEX_CONVERTER_CHAR(__QUEX_FROM, utf32)((const __QUEX_TYPE_FROM**)input_pp, output_pp); }

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(buffer, char)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                     char**                       output_pp);
{ __QUEX_CONVERTER_CHAR(__QUEX_FROM, char)((const __QUEX_TYPE_FROM**)input_pp, output_pp); }

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE void
    __QUEX_CONVERTER_CHAR(buffer, wchar_t)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                           wchar_t**                    output_pp);
    { __QUEX_CONVERTER_CHAR(__QUEX_FROM, wchar_t)((const __QUEX_TYPE_FROM**)input_pp, output_pp); }
#endif

/* (2) String converters */
QUEX_INLINE void
__QUEX_CONVERTER_STRING(buffer, utf8)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                      const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                      uint8_t**                    drain_pp,  
                                      const uint8_t*               DrainEnd)
{
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)((const __QUEX_TYPE_FROM**)  source_pp, 
                                                     (const __QUEX_TYPE_FROM*)   SourceEnd, 
                                                     drain_pp, DrainEnd);
}

QUEX_INLINE void
__QUEX_CONVERTER_STRING(buffer, utf16)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                       const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                       uint16_t**                   drain_pp,  
                                       const uint16_t*              DrainEnd)
{
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)((const __QUEX_TYPE_FROM**)source_pp, 
                                                      (const __QUEX_TYPE_FROM*)SourceEnd, 
                                                      drain_pp, DrainEnd);
}

QUEX_INLINE void
__QUEX_CONVERTER_STRING(buffer, utf32)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                       const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                       uint32_t**                   drain_pp,  
                                       const uint32_t*              DrainEnd);
{
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)((const __QUEX_TYPE_FROM**)source_pp, 
                                                      (const __QUEX_TYPE_FROM*)SourceEnd, 
                                                      drain_pp, DrainEnd);
}

QUEX_INLINE void
__QUEX_CONVERTER_STRING(buffer, char)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                       char**                       output_pp)
{
    __QUEX_CONVERTER_STRING(__QUEX_FROM, char)((const __QUEX_TYPE_FROM**)source_pp, 
                                                     (const __QUEX_TYPE_FROM*)SourceEnd, 
                                                     drain_pp, DrainEnd);
}
#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE void
    __QUEX_CONVERTER_STRING(buffer, wchar_t)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                              wchar_t**                 output_pp);
    {
        __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)((const __QUEX_TYPE_FROM**)source_pp, 
                                                            (const __QUEX_TYPE_FROM*)SourceEnd, 
                                                            drain_pp, DrainEnd);
    }
#endif

#if ! defined(__QUEX_OPTION_PLAIN_C)
    QUEX_INLINE std::basic_string<uint8_t>
    __QUEX_CONVERTER_STRING(buffer, utf8)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
    { return __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source); }
    QUEX_INLINE std::basic_string<uint16_t>
    __QUEX_CONVERTER_STRING(buffer, utf16)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
    { return __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source); }
    QUEX_INLINE std::basic_string<uint32_t>
    __QUEX_CONVERTER_STRING(buffer, utf32)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
    { return __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source); }
    QUEX_INLINE std::basic_string<char>
    __QUEX_CONVERTER_STRING(buffer, char)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
    { return __QUEX_CONVERTER_STRING(__QUEX_FROM, char)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source); }
#   if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
    QUEX_INLINE std::basic_string<wchar_t>
    __QUEX_CONVERTER_STRING(buffer, wchar_t)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
    { return __QUEX_CONVERTER_STRING(__QUEX_FROM, wchar_t)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source); }
#   endif
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I */
