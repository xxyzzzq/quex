/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I
#define  __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/stdint.h>
#include <quex/code_base/asserts>

#include <quex/code_base/converter_helper/quex_universal/utf8.i>
#include <quex/code_base/converter_helper/quex_universal/utf16.i>
#include <quex/code_base/converter_helper/quex_universal/utf32.i>

#if ! defined(__QUEX_OPTION_PLAIN_C)
namespace quex {
#endif

#define  __QUEX_G_DRAIN_NAME  utf8
#define  __QUEX_G_DRAIN_TYPE  uint8_t
#include <quex/code_base/converter_helper/generator/base-unicode.gi>

#define  __QUEX_G_DRAIN_NAME  utf16
#define  __QUEX_G_DRAIN_TYPE  uint16_t
#include <quex/code_base/converter_helper/generator/base-unicode.gi>

#define  __QUEX_G_DRAIN_NAME  utf32
#define  __QUEX_G_DRAIN_TYPE  uint32_t
#include <quex/code_base/converter_helper/generator/base-unicode.gi>

#if ! defined(__QUEX_OPTION_PLAIN_C)
} /* namespace quex */
#endif

#undef __QUEX_G_SOURCE_NAME
#undef __QUEX_G_SOURCE_TYPE

#endif /* __QUEX_INCLUDE_GUARD__CONVERTER_HELPER__UNICODE_I */
