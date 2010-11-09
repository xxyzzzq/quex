/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

/* Converter Functions: ____________________________________________________________________
 *
 *   $$CODEC$$_to_utf8(...)         -- character to utf8
 *   $$CODEC$$_to_utf8_string(...)  -- string to utf8
 *   $$CODEC$$_to_utf8_string(C++)  -- C++ string to utf8 (std::string)
 *
 *   $$CODEC$$_to_wchar(...)        -- character to utf8
 *   $$CODEC$$_to_wstring(...)      -- string to utf8
 *   $$CODEC$$_to_wstring(C++)      -- C++ string to utf8 (std::wstring)
 *__________________________________________________________________________________________*/

#ifndef   __QUEX_CONVERTER_FROM
#   error "__QUEX_CONVERTER_FROM must be defined."
#endif

#define __QUEX_TYPE_DRAIN    uint8_t
#define __QUEX_CONVERTER_TO  utf8_string
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint16_t
#define __QUEX_CONVERTER_TO  utf16_string
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint32_t
#define __QUEX_CONVERTER_TO  utf32_string
#include <quex/code_base/converter_helper/base-core.gi>

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                        const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                        wchar_t**                    drain_pp,  
                                                        const wchar_t*               DrainEnd)
{
#if   QUEX_SETTING_WCHAR_CODEC == UTF16
    __quex_assert(sizeof(wchar_t) == 2);
    __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf16_string)(source_pp,            SourceEnd, 
                                                                 (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
#elif QUEX_SETTING_WCHAR_CODEC == UTF32
    __quex_assert(sizeof(wchar_t) == 4);
    __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf32_string)(source_pp,            SourceEnd, 
                                                                 (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
#else
#     error "QUEX_SETTING_WCHAR_CODEC must be either 'UTF16' or 'UTF32'."
#endif
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::wstring
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
#if   QUEX_SETTING_WCHAR_CODEC == UTF16
    __quex_assert(sizeof(wchar_t) == 2);
    std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf16_string)(Source);

#elif QUEX_SETTING_WCHAR_CODEC == UTF32
    __quex_assert(sizeof(wchar_t) == 4);
    std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf32_string)(Source);
#else
#     error "QUEX_SETTING_WCHAR_CODEC must be either 'UTF16' or 'UTF32'."
#endif
    return std::wstring(tmp.c_str());
}
#endif

#undef __QUEX_CONVERTER_FROM
