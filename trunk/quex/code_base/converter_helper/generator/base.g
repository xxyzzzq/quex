/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * (C) 2005-2011 Frank-Rene Schaefer                                                */

/* Converter Functions: ____________________________________________________________________
 *
 *   $$CODEC$$_to_utf8(...)         -- character to utf8
 *   $$CODEC$$_to_utf8_string(...)  -- string to utf8
 *   $$CODEC$$_to_utf8_string(C++)  -- C++ string to utf8 (std::string)
 *
 *   $$CODEC$$_to_wchar(...)        -- character to wchar
 *   $$CODEC$$_to_wstring(...)      -- string to wchar
 *   $$CODEC$$_to_wstring(C++)      -- C++ string to wchar (std::wstring)
 *
 * $$CODEC$$ = '__QUEX_FROM' as defined by the including file.
 *__________________________________________________________________________________________*/

#ifndef __QUEX_FROM
#   error "__QUEX_FROM must be defined."
#endif

#define __QUEX_TYPE_DRAIN   uint8_t
#define __QUEX_TO           utf8
#include <quex/code_base/converter_helper/generator/base-core.g>

#define __QUEX_TYPE_DRAIN   uint16_t
#define __QUEX_TO           utf16
#include <quex/code_base/converter_helper/generator/base-core.g>

#define __QUEX_TYPE_DRAIN   uint32_t
#define __QUEX_TO           utf32
#include <quex/code_base/converter_helper/generator/base-core.g>

/* Note: 'char' and 'wchar_t' are mapped to 'utf8', 'utf16', 'utf32'
 *       depending on:
 *                         QUEX_SETTING_WCHAR_CODEC              
 *                         QUEX_SETTING_CHAR_CODEC                     */
#define __QUEX_TYPE_DRAIN   char
#define __QUEX_TO           char
#include <quex/code_base/converter_helper/generator/base-core.g>

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
#   define __QUEX_TYPE_DRAIN  wchar_t
#   define __QUEX_TO          wchar
#   include <quex/code_base/converter_helper/generator/base-core.g>
#endif

#undef __QUEX_FROM
#undef __QUEX_TYPE_SOURCE
