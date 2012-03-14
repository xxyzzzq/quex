/* -*- C++ -*- vim: set syntax=cpp:
 *
 * PURPOSE: 
 *
 * This file implements single character converter functions for conversions 
 *
 *            FROM utf16
 *            TO   utf8, utf16, and utf32
 *
 * That is, it implements the functions:
 *
 *            QUEX_CONVERTER_CHAR_DEF(utf16, utf8)(...)
 *            QUEX_CONVERTER_CHAR_DEF(utf16, utf16)(...)
 *            QUEX_CONVERTER_CHAR_DEF(utf16, utf32)(...)
 *
 * Those functions may be used by file "string-converter.gi" to implement
 * string converter functions.
 *
 * (C) 2005-2010 Frank-Rene Schaefer; ABSOLUTELY NO WARRANTY                      */
#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF16_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF16_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/asserts>

QUEX_NAMESPACE_QUEX_OPEN
#define __QUEX_CONVERTER_NAMESPACE quex

QUEX_INLINE void
QUEX_CONVERTER_CHAR_DEF(utf16, utf8)(const uint16_t** input_pp, uint8_t** output_pp)
{
    uint32_t  x0      = (uint16_t)0;
    uint32_t  x1      = (uint16_t)0;
    uint32_t  unicode = (uint32_t)0;

    if ( **input_pp <= (uint16_t)0x7f ) {
        *((*output_pp)++) = (uint8_t)*(*input_pp);
        ++(*input_pp);

    } else if ( **input_pp <= (uint16_t)0x7ff ) {
        *((*output_pp)++) = (uint8_t)(0xC0 | (*(*input_pp) >> 6)); 
        *((*output_pp)++) = (uint8_t)(0x80 | (*(*input_pp) & (uint16_t)0x3F));
        ++(*input_pp);

    } else if ( **input_pp < (uint16_t)0xD800 ) { 
        *((*output_pp)++) = (uint8_t)(0xE0 |  *(*input_pp)                    >> 12);
        *((*output_pp)++) = (uint8_t)(0x80 | (*(*input_pp) & (uint16_t)0xFFF) >> 6);
        *((*output_pp)++) = (uint8_t)(0x80 | (*(*input_pp) & (uint16_t)0x3F));
        ++(*input_pp);

    } else if ( **input_pp < (uint16_t)0xE000 ) { 
        /* Characters > 0xFFFF need to be coded in two bytes by means of surrogates. */
        x0 = (uint32_t)(*(*input_pp)++ - (uint32_t)0xD800);
        x1 = (uint32_t)(*(*input_pp)++ - (uint32_t)0xDC00);
        unicode = (x0 << 10) + x1 + 0x10000;

        /* Assume that only character appear, that are defined in unicode. */
        __quex_assert(unicode <= (uint16_t)0x1FFFFF);

        *((*output_pp)++) = (uint8_t)(0xF0 | unicode                       >> 18);
        *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3FFFF) >> 12);
        *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0xFFF)   >> 6);
        *((*output_pp)++) = (uint8_t)(0x80 | (unicode & (uint32_t)0x3F));

    } else { 
        /* Always true: **input_pp <= 0xFFFF */
        *((*output_pp)++) = (uint8_t)(0xE0 |  *(*input_pp)                    >> 12);
        *((*output_pp)++) = (uint8_t)(0x80 | (*(*input_pp) & (uint16_t)0xFFF) >> 6);
        *((*output_pp)++) = (uint8_t)(0x80 | (*(*input_pp) & (uint16_t)0x3F));
        ++(*input_pp);
    } 
}

QUEX_INLINE void
QUEX_CONVERTER_CHAR_DEF(utf16, utf16)(const uint16_t**  input_pp, 
                                      uint16_t**        output_pp)
{
    if( **input_pp < (uint16_t)0xD800 || **input_pp >= (uint16_t)0xE000 ) {
        *((*output_pp)++) = *(*input_pp)++;
    } else { 
        *((*output_pp)++) = *(*input_pp)++;
        *((*output_pp)++) = *(*input_pp)++;
    }
}

QUEX_INLINE void
QUEX_CONVERTER_CHAR_DEF(utf16, utf32)(const uint16_t**  input_pp, 
                                      uint32_t**        output_pp)
{
    uint32_t  x0 = (uint32_t)0;
    uint32_t  x1 = (uint32_t)0;

    if( **input_pp < (uint16_t)0xD800 || **input_pp >= (uint16_t)0xE000 ) {
        *((*output_pp)++) = *(*input_pp)++;
    } else { 
        x0 = (uint32_t)(*(*input_pp)++) - (uint32_t)0xD800;
        x1 = (uint32_t)(*(*input_pp)++) - (uint32_t)0xDC00;
        *((*output_pp)++) = (x0 << 10) + x1 + (uint32_t)0x10000;
    }
}

QUEX_NAMESPACE_QUEX_CLOSE
#undef __QUEX_CONVERTER_NAMESPACE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF16_I */

