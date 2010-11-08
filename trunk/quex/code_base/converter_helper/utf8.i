#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF8_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF8_I
/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

QUEX_NAMESPACE_MAIN_OPEN


QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
__QUEX_CONVERTER_HELPER(utf8, utf8)(const QUEX_TYPE_CHARACTER** input_pp, uint8_t** output_pp)
{
    /* Just for comformity with other encodings: Do nothing but copying. */
    if( (**input_pp & 0x80) == 0 ) {
        *(*output_pp)++ = *(*input_pp)++;
    }
    else if( **input_pp < 0xE0 ) { 
        *(*output_pp)++ = *(*input_pp)++;
        *(*output_pp)++ = *(*input_pp)++;
    }
    else if( **input_pp < 0xF0 ) { 
        *(*output_pp)++ = *(*input_pp)++;
        *(*output_pp)++ = *(*input_pp)++; 
        *(*output_pp)++ = *(*input_pp)++;
    }
    else {
        *(*output_pp)++ = *(*input_pp)++; 
        *(*output_pp)++ = *(*input_pp)++; 
        *(*output_pp)++ = *(*input_pp)++; 
        *(*output_pp)++ = *(*input_pp)++;
    }
}

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)

QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
__QUEX_CONVERTER_HELPER(utf8, wchar)(const QUEX_TYPE_CHARACTER** input_pp, wchar_t** output_pp)
{
    const QUEX_TYPE_CHARACTER*  iterator = *input_pp;

    if( (*iterator & 0x80) == 0 ) {
        /* Header: 0xxx.xxxx */
        **output_pp = (wchar_t)*(iterator++);
    }
    else if( *iterator < 0xE0 ) { /* ... max: 1101.1111 --> 0xDF, next: 0xE0 */
        /*    110x.xxxx 10yy.yyyy 
         * => 0000.0xxx:xxyy.yyyy  */
        **output_pp  = ( ((wchar_t)*(iterator++)) & 0x1F ) << 6;
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F );
    }
    else if( *iterator < 0xF0 ) { /* ... max: 1110.1111 --> 0xEF, next: 0xF0 */
        /*    1110.xxxx 10yy.yyyy 10zz.zzzz
         * => xxxx.yyyy:yyzz.zzzz           */
        **output_pp  = ( ((wchar_t)*(iterator++)) & 0x0F ) << 12;
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F ) << 6; 
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F );
    }
    else {
        /* Unicode standard defines only chars until 0x10ffff, so max(len(utf8char)) == 4.
         *
         * NO CHECK: if( *iterator < 0xF8 ) { ... max: 1111.0111 --> 0xF7, next: 0xF8 
         *
         *    1111.0uuu 10xx.xxxx 10yy.yyyy 10zz.zzzz
         * => 000u.uuxx:xxxx.yyyy:yyzz.zzzz           */
        **output_pp  = ( ((wchar_t)*(iterator++)) & 0x07 ) << 18; 
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F ) << 12; 
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F ) << 6; 
        **output_pp |= ( ((wchar_t)*(iterator++)) & 0x3F );
    }
    ++(*output_pp);
    *input_pp = iterator;
}
#endif /* ! __QUEX_OPTION_WCHAR_T_DISABLED */

QUEX_NAMESPACE_MAIN_CLOSE

#define __QUEX_CONVERTER_FROM   utf8
#include <quex/code_base/converter_helper/base.gi>

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF8_I */
