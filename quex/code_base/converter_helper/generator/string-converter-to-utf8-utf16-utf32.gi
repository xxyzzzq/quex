/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#ifndef    __QUEX_G_SOURCE_NAME
#   error "__QUEX_G_SOURCE_NAME must be defined."
#endif
#ifndef    __QUEX_G_SOURCE_TYPE
#   error "__QUEX_G_SOURCE_TYPE must be defined."
#endif

/* NOTE: '__QUEX_MAX_CHAR_SIZE' referes to the maximum number of chunks.
 *       For utf8 the 'chunks' are bytes. For utf16 the 'chunks' are 
 *       two byte long. For utf32 the chunks are 4 byte long. Thus, the
 *       numbers for __QUEX_MAX_CHAR_SIZE as seen below.                   */
#define __QUEX_TYPE_DRAIN    uint8_t
#define __QUEX_TO            utf8
#define __QUEX_MAX_CHAR_SIZE 4
#include <quex/code_base/converter_helper/generator/string-converter.gi>

#define __QUEX_TYPE_DRAIN    uint16_t
#define __QUEX_TO            utf16
#define __QUEX_MAX_CHAR_SIZE 2
#include <quex/code_base/converter_helper/generator/string-converter.gi>

#define __QUEX_TYPE_DRAIN    uint32_t
#define __QUEX_TO            utf32
#define __QUEX_MAX_CHAR_SIZE 1
#include <quex/code_base/converter_helper/generator/string-converter.gi>

#undef __QUEX_G_SOURCE_NAME
#undef __QUEX_G_SOURCE_TYPE 

