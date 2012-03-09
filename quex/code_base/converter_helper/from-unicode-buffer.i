/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Provide the implementation of character and string converter functions
 * FROM the buffer's unicode to utf8, utf16, utf32, char, and wchar_t.
 *
 * STEPS:
 *
 * (1) Include the implementation of the character converters from the 
 *     buffer's unicode to utf8, utf16, utf32, char, and wchar_t. For
 *     this it is relied upon one of the character converter families
 *     from utf8, utf16, or utf32. Depending on the size of QUEX_TYPE_CHARACTER
 *     the correspondent converters are included, that is one of:
 *
 *             "character-converter-from-utf8.i"
 *             "character-converter-from-utf16.i"
 *             "character-converter-from-utf32.i"
 *
 * (1b) The 'char' and 'wchar_t' converters are defined in terms of those
 *      as usual relying on:
 *
 *             "../generator/character-converter-char-wchar_t.gi"
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
 * These functions ARE DEPENDENT on QUEX_TYPE_CHARACTER.
 * => Thus, they are placed in the analyzer's namespace.
 *
 * 2010 (C) Frank-Rene Schaefer; 
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I

#include <quex/code_base/definitions>
#include <quex/code_base/asserts>

QUEX_NAMESPACE_MAIN_OPEN

/* (1) Implement the character converters utf8, utf16, utf32.
 *     (Note, that character converters are generated into namespace 'quex'.)*/
#if   QUEX_SETTING_CHARACTER_SIZE == 1
#    include <quex/code_base/converter_helper/universal/from-utf8.i>
#    define __QUEX_FROM       utf8
#    define __QUEX_FROM_TYPE  uint8_t
#elif QUEX_SETTING_CHARACTER_SIZE == 2
#    include <quex/code_base/converter_helper/universal/from-utf16.i>
#    define __QUEX_FROM       utf16
#    define __QUEX_FROM_TYPE  uint16_t
#elif QUEX_SETTING_CHARACTER_SIZE == 4
#    include <quex/code_base/converter_helper/universal/from-utf32.i>
#    define __QUEX_FROM       utf32
#    define __QUEX_FROM_TYPE  uint32_t
#else
#    error "Unfortunately, no character converter can be provided for the buffer's codec."
#endif

/* (1b) Derive converters to char and wchar_t from the given set 
 *      of converters. (Generator uses __QUEX_FROM and QUEX_FROM_TYPE)      */
#include <quex/code_base/converter_helper/generator/character-converter-char-wchar_t.gi>

/* (2) Generate string converters to utf8, utf16, utf32 based on the
 *     definitions of the character converters.                             */
#include <quex/code_base/converter_helper/generator/string-converters-to-utf8-utf16-utf32-char-wchar_t.gi>

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I */
