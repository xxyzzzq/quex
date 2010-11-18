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
__QUEX_CONVERTER_CHAR($$CODEC$$, utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                       uint8_t**                    output_pp)
{
$$PROLOG_UTF8$$
    uint32_t   unicode = (uint32_t)-1;

    QUEX_TYPE_CHARACTER input = *(*input_pp)++;
    
$$BODY_UTF8$$

one_byte:
    *((*output_pp)++) = (uint8_t)unicode;
    return;

two_bytes:
    *((*output_pp)++) = (uint8_t)(0xC0 | (unicode >> 6)); 
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3f));
    return;

three_bytes:
    *((*output_pp)++) = (uint8_t)(0xE0 | unicode           >> 12);
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0xFFF) >> 6);
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3F));
    return;

four_bytes:
    /* Assume that only character appear, that are defined in unicode. */
    __quex_assert(unicode <= (uint32_t)0x1FFFFF);
    /* No surrogate pairs (They are reserved even in non-utf16).       */
    __quex_assert(! (unicode >= 0xd800 && unicode <= 0xdfff) );

    *((*output_pp)++) = (uint8_t)(0xF0 | unicode >> 18);
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3FFFF) >> 12);
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0xFFF)   >> 6);
    *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3F));
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR($$CODEC$$, utf16)(const QUEX_TYPE_CHARACTER** input_pp,
                                        uint16_t**                  output_pp)
{
    uint16_t             unicode = 0L;
    QUEX_TYPE_CHARACTER  input = *(*input_pp)++;
$$BODY_UTF16$$
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR($$CODEC$$, utf32)(const QUEX_TYPE_CHARACTER** input_pp,
                                        uint32_t**                  output_pp)
{
    uint32_t             unicode = 0L;
    QUEX_TYPE_CHARACTER  input = *(*input_pp)++;
$$BODY_UTF32$$
}

QUEX_NAMESPACE_MAIN_CLOSE

#define __QUEX_FROM         $$CODEC$$
#define __QUEX_TYPE_SOURCE  QUEX_TYPE_CHARACTER
#include <quex/code_base/converter_helper/base.gi>



#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__$$CODEC$$_I */

