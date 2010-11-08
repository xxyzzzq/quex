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
 *   $$CODEC$$_to_wchar(...)        -- character to utf8
 *   $$CODEC$$_to_wstring(...)      -- string to utf8
 *   $$CODEC$$_to_wstring(C++)      -- C++ string to utf8 (std::wstring)
 *__________________________________________________________________________________________*/

#ifndef __QUEX_CONVERTER_FROM
#   error "__QUEX_CONVERTER_FROM must be defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8_string)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                            const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                            uint8_t**                    drain_pp,  
                                                            const uint8_t*               DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::string
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8_string)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
#endif


#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                        const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                        uint8_t**                    drain_pp,  
                                                        const uint8_t*               DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::wstring
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
#endif

#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_CONVERTER_FROM
