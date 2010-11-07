/* Configure this header by defining one of:
 *
 *    TEST_UTF8, TEST_UTF16, TEST_UNICODE, TEST_CODEC
 *                                                      */
#ifndef __INCLUDE_GUARD__COMMON_H
#define __INCLUDE_GUARD__COMMON_H

#define QUEX_NAMESPACE_MAIN_OPEN  namespace Tester {
#define QUEX_NAMESPACE_MAIN_CLOSE }

#define ____QUEX_CONVERTER_HELPER(A, B) Testy_from_ ## A ## _to_ ## B
#define __QUEX_CONVERTER_HELPER(A, B)   ____QUEX_CONVERTER_HELPER(A, B)

#if   defined(TEST_UTF8)
#  define  FROM_CODEC           utf8
#  define  QUEX_TYPE_CHARACTER  uint8_t
#  include <quex/code_base/converter_helper/utf8>
#  include <quex/code_base/converter_helper/utf8.i>
#elif defined(TEST_UTF16)
#  define  FROM_CODEC           utf16
#  define  QUEX_TYPE_CHARACTER  uint16_t
#  include <quex/code_base/converter_helper/utf16>
#  include <quex/code_base/converter_helper/utf16.i>
#elif defined(TEST_UTF16)
#elif defined(TEST_UNICODE)
#  define  FROM_CODEC           unicode
#  define  QUEX_TYPE_CHARACTER  uint32_t
#  include <quex/code_base/converter_helper/unicode>
#  include <quex/code_base/converter_helper/unicode.i>
#elif defined(TEST_CODEC)
#else
#  error "No test codec defined."
#endif

#define CONVERTER(OUTPUT)   Tester::__QUEX_CONVERTER_HELPER(FROM_CODEC, OUTPUT)

using namespace std;
#include <iostream>

extern void 
test_utf8_string(const char*                 TestName, 
                 const QUEX_TYPE_CHARACTER*  source_p,  const QUEX_TYPE_CHARACTER*  SourceEnd,
                 size_t                      DrainSize, const uint8_t*              reference);
extern void 
test_wstring(const char*                 TestName, 
             const QUEX_TYPE_CHARACTER*  source_p,  const QUEX_TYPE_CHARACTER*  SourceEnd,
             size_t                      DrainSize, const wchar_t*              reference);

#endif /* __INCLUDE_GUARD__COMMON_H */
