/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Provide the implementation of character and string converter functions
 * FROM utf16 to utf8, utf16, and utf32.
 *
 * Before string converter functions are generated through file 
 * 'string-converter.gi' the character functions are included from 
 * 'character-converter-utf16.i'.
 *
 * All functions in this file are universal and not dependent on the
 * analyzer or buffer element type. Thus, they are placed in namespace 'quex'.
 *
 * 2010 (C) Frank-Rene Schaefer; 
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I

/* (1) Implement the character converters from utf16 to utf8, utf16, utf32.
 *     (Note, that character converters are generated into namespace 'quex'.)*/
#include <quex/code_base/converter_helper/quex_universal/character-converter-utf16.i>

/* (2) Generate string converters from utf16 to utf8, utf16, utf32 based on the
 *     definitions of 
 *
 *            __QUEX_CONVERTER_CHAR(utf16, utf8)(...)
 *            __QUEX_CONVERTER_CHAR(utf16, utf16)(...)
 *            __QUEX_CONVERTER_CHAR(utf16, utf32)(...)
 *
 *     which have been defined in (1).                                       */

#if ! defined(__QUEX_OPTION_PLAIN_C)
namespace quex {
#endif

#define __QUEX_FROM          utf16
#define __QUEX_TYPE_SOURCE   uint16_t

#define __QUEX_TO            utf8
#define __QUEX_TYPE_DRAIN    uint8_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>
#define __QUEX_TO            utf16
#define __QUEX_TYPE_DRAIN    uint16_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>
#define __QUEX_TO            utf32
#define __QUEX_TYPE_DRAIN    uint32_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>

#if ! defined(__QUEX_OPTION_PLAIN_C)
} /* namespace quex */
#endif

/* 'string-converter.gi' is so kind not to undef __QUEX_FROM and 
 * __QUEX_TYPE_SOURCE, so we do it here.                                     */
#undef __QUEX_FROM
#undef __QUEX_TYPE_SOURCE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I */
