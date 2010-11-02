/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I

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

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME($$CODEC$$_to_utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                             uint8_t**                    output_pp)
{
$$PROLOG_UTF8$$
    uint32_t   unicode  = 0xFFFF;
    uint8_t*   output_p = *output_pp;
    uint8_t*   p        = output_p;

    QUEX_TYPE_CHARACTER input = **input_pp;
    
    /* The unicode range simply does not go beyond 0x10FFFF */
    __quex_assert(input < 0x110000);
    /* If the following assert fails, then QUEX_TYPE_CHARACTER needs to be chosen
     * of 'unsigned' type, e.g. 'unsigned char' instead of 'char'.                */
    /* __quex_assert(input >= 0); */

#if 0
#   if defined(__QUEX_OPTION_LITTLE_ENDIAN)
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 3 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 0 ))
#   else                             
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 0 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 3 ))
#   endif
#else
#   define QUEX_BYTE_0  ((uint8_t)((unicode & 0xFF)))
#   define QUEX_BYTE_1  ((uint8_t)((unicode & 0xFF00) >> 8))
#   define QUEX_BYTE_2  ((uint8_t)((unicode & 0xFF0000) >> 16))
#   define QUEX_BYTE_3  ((uint8_t)((unicode & 0xFF000000) >> 24))
#endif

$$BODY_UTF8$$
    __quex_assert(p - output_p < (ptrdiff_t)7);
    __quex_assert(p > output_p);
    *output_pp = p;
    ++(*input_pp);

#   undef QUEX_BYTE_0 
#   undef QUEX_BYTE_1 
#   undef QUEX_BYTE_2 
#   undef QUEX_BYTE_3 
}

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)

QUEX_INLINE void
QUEX_NAME($$CODEC$$_to_wchar)(const QUEX_TYPE_CHARACTER** input_pp,
                              wchar_t**                   output_pp)
{
    uint32_t             unicode = 0L;
    QUEX_TYPE_CHARACTER  input = **input_pp;
$$BODY_UCS4$$
    ++(*input_pp);
    ++(*output_pp);
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#define __QUEX_CONVERTER_FROM     $$CODEC$$
#include <quex/code_base/converter_helper/base.gi>



#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I */

