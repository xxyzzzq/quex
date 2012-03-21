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
 *            QUEX_CONVERTER_CHAR_DEF(utf8, utf8)(...)
 *            QUEX_CONVERTER_CHAR_DEF(utf8, utf16)(...)
 *            QUEX_CONVERTER_CHAR_DEF(utf8, utf32)(...)
 *
 * Those functions may be used by file "string-converter.gi" to implement
 * string converter functions.
 *
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER__FROM_UTF8_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER__FROM_UTF8_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/asserts>

QUEX_NAMESPACE_MAIN_OPEN


QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__CHARACTER_CONVERTER__FROM_UTF8_I */
