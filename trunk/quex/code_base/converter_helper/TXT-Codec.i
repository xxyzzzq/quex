/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
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

#if ! defined(__QUEX_OPTION_PLAIN_C)
namespace quex {
#endif

QUEX_INLINE void
__QUEX_CONVERTER_CHAR($$CODEC$$, utf32)(const QUEX_TYPE_CHARACTER** input_pp,
                                        uint32_t**                  output_pp)
{
    uint16_t             unicode = (uint32_t)0;
    QUEX_TYPE_CHARACTER  input   = *(*input_pp)++;
$$BODY_UTF32$$
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR($$CODEC$$, utf16)(const QUEX_TYPE_CHARACTER** input_pp,
                                        uint16_t**                  output_pp)
{
    uint32_t   unicode   = (uint32_t)0;
    uint32_t*  unicode_p = &unicode;

    __QUEX_CONVERTER_CHAR($$CODEC$$, utf32)(input_pp, &unicode_p);
$$BODY_UTF16$$
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR($$CODEC$$, utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                       uint8_t**                    output_pp)
{
    uint32_t            unicode = (uint32_t)-1;
    QUEX_TYPE_CHARACTER input   = *(*input_pp)++;
    
$$BODY_UTF8$$

$$EPILOG$$
}

#define  __QUEX_G_SOURCE_NAME  $$CODEC$$
#define  __QUEX_G_SOURCE_TYPE  QUEX_TYPE_CHARACTER
#include <quex/code_base/converter_helper/generator/string-converter-to-utf8-utf16-utf32.gi>

#define __QUEX_TO             char
#define __QUEX_TYPE_DRAIN     char
#define __QUEX_DRAIN_CODEC    QUEX_SETTING_CHAR_CODEC
#include <quex/code_base/converter_helper/generator/string-converter-to-char-and-wchar.gi>

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
#   define __QUEX_TO             wchar_t
#   define __QUEX_TYPE_DRAIN     wchar_t
#   define __QUEX_DRAIN_CODEC    QUEX_SETTING_WCHAR_CODEC
#   include <quex/code_base/converter_helper/generator/string-converter-to-char-and-wchar.gi>
#endif

#if ! defined(__QUEX_OPTION_PLAIN_C)
} /* namespace quex */
#endif



#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I */

