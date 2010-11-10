#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I
/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer; ABSOLUTELY NO WARRANTY                      */
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>


QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(utf16, utf8)(const QUEX_TYPE_CHARACTER** input_pp, uint8_t** output_pp)
{
    uint16_t  x0      = (uint16_t)0;
    uint16_t  x1      = (uint16_t)0;
    uint32_t  unicode = (uint16_t)0;

    if ( **input_pp <= 0x7f ) {
        *(*output_pp)++ = (uint8_t)*(*input_pp);
        ++(*input_pp);

    } else if ( **input_pp <= 0x7ff ) {
        *(*output_pp)++ = (uint8_t)(0xC0 | (*(*input_pp) >> 6)); 
        *(*output_pp)++ = (uint8_t)(0x80 | (*(*input_pp) & 0x3f));
        ++(*input_pp);

    } else if ( **input_pp < 0xD800 ) { 
        *(*output_pp)++ = (uint8_t)(0xE0 |  *(*input_pp)           >> 12);
        *(*output_pp)++ = (uint8_t)(0x80 | (*(*input_pp) & 0xFFF) >> 6);
        *(*output_pp)++ = (uint8_t)(0x80 | (*(*input_pp) & 0x3F));
        ++(*input_pp);

    } else if ( **input_pp < 0xE000 ) { 
        /* Characters > 0xFFFF need to be coded in two bytes by means of surrogates. */
        x0 = *(*input_pp)++ - 0xD800;
        x1 = *(*input_pp)++ - 0xDC00;
        unicode = (x0 << 10) + x1 + 0x10000;

        /* Assume that only character appear, that are defined in unicode. */
        __quex_assert(unicode <= (QUEX_TYPE_CHARACTER)0x1FFFFF);

        *(*output_pp)++ = (uint8_t)(0xF0 | unicode >> 18);
        *(*output_pp)++ = (uint8_t)(0x80 | (unicode & 0x3FFFF) >> 12);
        *(*output_pp)++ = (uint8_t)(0x80 | (unicode & 0xFFF)   >> 6);
        *(*output_pp)++ = (uint8_t)(0x80 | (unicode & 0x3F));

    } else { 
        __quex_assert( **input_pp <= 0xFFFF); /* Note, in UTF16 no single value > 0xFFFF */
        *(*output_pp)++ = (uint8_t)(0xE0 |  *(*input_pp)          >> 12);
        *(*output_pp)++ = (uint8_t)(0x80 | (*(*input_pp) & 0xFFF) >> 6);
        *(*output_pp)++ = (uint8_t)(0x80 | (*(*input_pp) & 0x3F));
        ++(*input_pp);
    } 
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(utf16, utf16)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                    uint16_t**                   output_pp)
{
    if( **input_pp < 0xD800 || **input_pp > 0xE000 ) {
        *(*output_pp)++ = *(*input_pp)++;
    } else { 
        *(*output)++ = *(*input_pp)++ - 0xD800;
        *(*output)++ = *(*input_pp)++ - 0xDC00;
    }
}

QUEX_INLINE void
__QUEX_CONVERTER_CHAR(utf16, utf32)(const QUEX_TYPE_CHARACTER**  input_pp, 
                                    uint32_t**                   output_pp)
{
    uint32_t  x0 = (wchar_t)0;
    uint32_t  x1 = (wchar_t)0;

    if( **input_pp < 0xD800 || **input_pp > 0xE000 ) {
        *(*output_pp)++ = *(*input_pp)++;
    } else { 
        x0 = *(*input_pp)++ - 0xD800;
        x1 = *(*input_pp)++ - 0xDC00;
        *(*output_pp)++ = (x0 << 10) + x1 + 0x10000;
    }
}

QUEX_NAMESPACE_MAIN_CLOSE

#define __QUEX_FROM  utf16
#include <quex/code_base/converter_helper/base.gi>

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I */

