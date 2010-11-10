/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>
#if ! defined(__QUEX_OPTION_PLAIN_C)
#   include <string>
#endif

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

#ifndef   __QUEX_FROM
#   error "__QUEX_FROM must be defined."
#endif

#define __QUEX_TYPE_DRAIN    uint8_t
#define __QUEX_TO            utf8
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint16_t
#define __QUEX_TO            utf16
#include <quex/code_base/converter_helper/base-core.gi>

#define __QUEX_TYPE_DRAIN    uint32_t
#define __QUEX_TO            utf32
#include <quex/code_base/converter_helper/base-core.gi>

/* Adapt 'char' and 'wchar_t' to utf8, utf16 or utf32 depending on its size. */
#define __QUEX_TYPE_DRAIN    char
#define __QUEX_TO            char
#define __QUEX_MAP_TO_CODEC  QUEX_SETTING_CHAR_CODEC
#include <quex/code_base/converter_helper/base-char-and-wchar.gi>

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
#   define __QUEX_TYPE_DRAIN    wchar_t
#   define __QUEX_TO            wchar
#   define __QUEX_MAP_TO_CODEC  QUEX_SETTING_WCHAR_CODEC
#   include <quex/code_base/converter_helper/base-char-and-wchar.gi>
#endif 

#undef __QUEX_FROM
