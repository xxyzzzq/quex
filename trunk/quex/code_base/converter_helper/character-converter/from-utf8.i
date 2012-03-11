/* -*- C++ -*- vim: set syntax=cpp:
 *
 * PURPOSE: 
 *
 * This file implements single character converter functions for conversions 
 *
 *            FROM utf8
 *            TO   utf8, utf16, and utf32
 *
 * That is, it implements the functions:
 *
 *            __QUEX_CONVERTER_CHAR(utf8, utf8)(...)
 *            __QUEX_CONVERTER_CHAR(utf8, utf16)(...)
 *            __QUEX_CONVERTER_CHAR(utf8, utf32)(...)
 *
 * Those functions may be used by file "string-converter.gi" to implement
 * string converter functions.
 *
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF8_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF8_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/asserts>

#if ! defined(__QUEX_OPTION_PLAIN_C)
namespace quex {
#endif

QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
__QUEX_CONVERTER_CHAR(utf8, utf8)(const uint8_t** input_pp, uint8_t** output_pp)
{
    /* Just for comformity with other encodings: Do nothing but copying. */
    if( (**input_pp & (uint8_t)0x80) == (uint8_t)0 ) {
        *((*output_pp)++) = *(*input_pp)++;
    }
    else if( **input_pp < (uint8_t)0xE0 ) { 
        *((*output_pp)++) = *(*input_pp)++;
        *((*output_pp)++) = *(*input_pp)++;
    }
    else if( **input_pp < (uint8_t)0xF0 ) { 
        *((*output_pp)++) = *(*input_pp)++;
        *((*output_pp)++) = *(*input_pp)++; 
        *((*output_pp)++) = *(*input_pp)++;
    }
    else {
        *((*output_pp)++) = *(*input_pp)++; 
        *((*output_pp)++) = *(*input_pp)++; 
        *((*output_pp)++) = *(*input_pp)++; 
        *((*output_pp)++) = *(*input_pp)++;
    }
}

QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
__QUEX_CONVERTER_CHAR(utf8, utf16)(const uint8_t** input_pp, uint16_t** output_pp)
{
    const uint8_t*  iterator = *input_pp;
    uint32_t        tmp = 0;

    if( (*iterator & (uint8_t)0x80) == (uint8_t)0 ) {
        /* Header: 0xxx.xxxx */
        **output_pp = (uint16_t)*(iterator++);

        ++(*output_pp);
    }
    else if( *iterator < (uint8_t)0xE0 ) { /* ... max: 1101.1111 --> 0xDF, next: 0xE0               */
        /*    110x.xxxx 10yy.yyyy 
         * => 0000.0xxx:xxyy.yyyy                                                          */
        **output_pp = (uint16_t)(( ((uint16_t)*(iterator++)) & (uint16_t)0x1F ) << 6);
        **output_pp = (uint16_t)((**output_pp) | (( ((uint16_t)*(iterator++)) & (uint16_t)0x3F )));

        ++(*output_pp);
    }
    else if( *iterator < (uint8_t)0xF0 ) { /* ... max: 1110.1111 --> 0xEF, next: 0xF0               */
        /*    1110.xxxx 10yy.yyyy 10zz.zzzz
         * => xxxx.yyyy:yyzz.zzzz                                                          */
        **output_pp = (uint16_t)(( ((uint16_t)*(iterator++)) & (uint16_t)0x0F ) << 12);
        **output_pp = (uint16_t)((**output_pp) | (( ((uint16_t)*(iterator++)) & (uint16_t)0x3F ) << 6)); 
        **output_pp = (uint16_t)((**output_pp) | (( ((uint16_t)*(iterator++)) & (uint16_t)0x3F )));

        ++(*output_pp);
    }
    else {
        /* Unicode standard defines only chars until 0x10ffff, so max(len(utf8char)) == 4.
         *
         * NO CHECK: if( *iterator < 0xF8 ) { ... max: 1111.0111 --> 0xF7, next: 0xF8 
         *
         *    1111.0uuu 10xx.xxxx 10yy.yyyy 10zz.zzzz
         * => 000u.uuxx:xxxx.yyyy:yyzz.zzzz                                                */

        /* It happens that the UTF8 domain with 4 bytes is >= 0x10000 which is the
         * starting domain for surrogates (i.e. what is mapped into 0xD800-0xE000         */
        tmp = (uint32_t)(      (((uint32_t)*(iterator++)) & (uint32_t)0x07 ) << 18); 
        tmp = (uint32_t)(tmp | (((uint32_t)*(iterator++)) & (uint32_t)0x3F ) << 12); 
        tmp = (uint32_t)(tmp | (((uint32_t)*(iterator++)) & (uint32_t)0x3F ) << 6); 
        tmp = (uint32_t)(tmp | (((uint32_t)*(iterator++)) & (uint32_t)0x3F ));

        tmp               = (uint32_t)(tmp - (uint32_t)0x10000);
        *((*output_pp)++) = (uint16_t)((tmp >> 10)             | (uint32_t)0xD800);
        *((*output_pp)++) = (uint16_t)((tmp & (uint32_t)0x3FF) | (uint32_t)0xDC00);
    }
    *input_pp = iterator;
}

QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
__QUEX_CONVERTER_CHAR(utf8, utf32)(const uint8_t** input_pp, uint32_t** output_pp)
{
    const uint8_t*  iterator = *input_pp;

    if( (*iterator & (uint8_t)0x80) == (uint8_t)0 ) {
        /* Header: 0xxx.xxxx */
        **output_pp = (uint32_t)*(iterator++);
    }
    else if( *iterator < (uint8_t)0xE0 ) { /* ... max: 1101.1111 --> 0xDF, next: 0xE0               */
        /*    110x.xxxx 10yy.yyyy 
         * => 0000.0xxx:xxyy.yyyy                                                          */
        **output_pp = (                          ( ((uint32_t)*(iterator++)) & (uint32_t)0x1F ) << 6);
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ));
    }
    else if( *iterator < (uint8_t)0xF0 ) { /* ... max: 1110.1111 --> 0xEF, next: 0xF0               */
        /*    1110.xxxx 10yy.yyyy 10zz.zzzz
         * => xxxx.yyyy:yyzz.zzzz                                                          */
        **output_pp = (                          ( ((uint32_t)*(iterator++)) & (uint32_t)0x0F ) << 12);
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ) << 6); 
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ));
    }
    else {
        /* Unicode standard defines only chars until 0x10ffff, so max(len(utf8char)) == 4.
         *
         * NO CHECK: if( *iterator < 0xF8 ) { ... max: 1111.0111 --> 0xF7, next: 0xF8 
         *
         *    1111.0uuu 10xx.xxxx 10yy.yyyy 10zz.zzzz
         * => 000u.uuxx:xxxx.yyyy:yyzz.zzzz                                                */
        **output_pp = (                          ( ((uint32_t)*(iterator++)) & (uint32_t)0x07 ) << 18); 
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ) << 12); 
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ) << 6); 
        **output_pp = (uint32_t)((**output_pp) | ( ((uint32_t)*(iterator++)) & (uint32_t)0x3F ));
    }
    ++(*output_pp);
    *input_pp = iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
} /* namespace quex */
#endif

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER_UTF8_I */
