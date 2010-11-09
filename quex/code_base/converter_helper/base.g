/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
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
 *   $$CODEC$$_to_wchar(...)        -- character to wchar
 *   $$CODEC$$_to_wstring(...)      -- string to wchar
 *   $$CODEC$$_to_wstring(C++)      -- C++ string to wchar (std::wstring)
 *__________________________________________________________________________________________*/

#ifndef __QUEX_CONVERTER_FROM
#   error "__QUEX_CONVERTER_FROM must be defined."
#endif


#define __QUEX_TYPE_DRAIN   uint8_t
#define __QUEX_CONVERTER_TO utf8_string
#include <quex/code_base/converter_helper/base-core.g>

#define __QUEX_TYPE_DRAIN   uint16_t
#define __QUEX_CONVERTER_TO utf16_string
#include <quex/code_base/converter_helper/base-core.g>

#define __QUEX_TYPE_DRAIN   uint32_t
#define __QUEX_CONVERTER_TO utf32_string
#include <quex/code_base/converter_helper/base-core.g>

/* Note: 'wchar_t' is mapped to either utf16 or utf32 depending on
 *       QUEX_SETTING_WCHAR_CODEC                                  */
#define __QUEX_TYPE_DRAIN     wchar_t
#define __QUEX_CONVERTER_TO   wstring
#include <quex/code_base/converter_helper/base-core.g>

#undef __QUEX_CONVERTER_FROM
