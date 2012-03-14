/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Provide the implementation of character and string converter functions
 * FROM utf16 to utf8, utf16, utf32, char, and wchar_t.
 *
 * STEPS:
 *
 * (1) Include the implementation of the character converters from utf16 
 *     to utf8, utf16, utf32, char, and wchar_t.
 *
 *     Use: "character-converter/from-utf16.i"
 *             --> implementation for utf16
 *
 *          "../generator/character-converter-char-wchar_t.gi"
 *             --> route 'char' and 'wchar_t' conversion to
 *                 one of the converters defined before.
 *
 * (2) Generate the implementation of the string converters in terms
 *     of those character converters.
 *
 *     Use: "../generator/implementation-string-converters.gi"
 *
 *          which uses
 *
 *              "../generator/string-converter.gi"
 *
 *          to implement each string converter from the given 
 *          character converters. 
 *
 * All functions in this file are universal and not dependent on the
 * analyzer or buffer element type. Thus, they are placed in namespace 'quex'.
 *
 * 2010 (C) Frank-Rene Schaefer; 
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I
#define __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I

#define __QUEX_FROM       utf16
#define __QUEX_FROM_TYPE  uint16_t

/* (1) Implement the character converters utf8, utf16, utf32.
 *     (Note, that character converters are generated into namespace 'quex'.)*/
#include <quex/code_base/converter_helper/character-converter/from-utf16.i>

QUEX_NAMESPACE_QUEX_OPEN
#define __QUEX_CONVERTER_NAMESPACE quex

/* (1b) Derive converters to char and wchar_t from the given set 
 *      of converters. (Generator uses __QUEX_FROM and QUEX_FROM_TYPE)      */
#include <quex/code_base/converter_helper/generator/character-converter-to-char-wchar_t.gi>

/* (2) Generate string converters to utf8, utf16, utf32 based on the
 *     definitions of the character converters.                             */
#include <quex/code_base/converter_helper/generator/implementations.gi>

QUEX_NAMESPACE_QUEX_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UTF16_I */
