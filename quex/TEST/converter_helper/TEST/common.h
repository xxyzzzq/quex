/* Configure this header by defining one of:
 *
 *    TEST_UTF8, TEST_UTF16, TEST_UNICODE, TEST_CODEC
 *                                                      */
#ifndef __INCLUDE_GUARD__COMMON_H
#define __INCLUDE_GUARD__COMMON_H

#define QUEX_NAMESPACE_MAIN_OPEN  namespace Tester {
#define QUEX_NAMESPACE_MAIN_CLOSE }

#define ____QUEX_CONVERTER_CHAR(FROM, TO)    Tester_ ## FROM ## _to_ ## TO ## _character
#define __QUEX_CONVERTER_CHAR(FROM, TO)      ____QUEX_CONVERTER_CHAR(FROM, TO)
#define ____QUEX_CONVERTER_STRING(FROM, TO)  Tester_ ## FROM ## _to_ ## TO
#define __QUEX_CONVERTER_STRING(FROM, TO)    ____QUEX_CONVERTER_STRING(FROM, TO)

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

#define CONVERTER(OUTPUT)   Tester::__QUEX_CONVERTER_STRING(FROM_CODEC, OUTPUT)

using namespace std;
#include <iostream>
#include <cstdio>
#include <cstdlib>

extern void 
test_utf8_string(const char*                 TestName, 
                 const QUEX_TYPE_CHARACTER*  source_p,  const QUEX_TYPE_CHARACTER*  SourceEnd,
                 size_t                      DrainSize, const uint8_t*              reference);
extern void 
test_wstring(const char*                 TestName, 
             const QUEX_TYPE_CHARACTER*  source_p,  const QUEX_TYPE_CHARACTER*  SourceEnd,
             size_t                      DrainSize, const wchar_t*              reference);

template <class ElementT> inline ElementT*
read_from_file(ElementT* buffer, size_t Size, const char* FileName)
{
    using namespace std;

    ElementT*   iterator  = buffer;
    ElementT*   BufferEnd = buffer + Size;

    FILE*  fh = fopen(FileName, "rb");
    if( fh == NULL ) {
        printf("File '%s' not found!", FileName);
        exit(-1);
    }

    do {
        uint8_t  bytes[sizeof(ElementT)]; 
        for(int i = 0; i < sizeof(ElementT); ++i) {
            int tmp = fgetc(fh);
            if( tmp == EOF ) goto Exit;
            bytes[sizeof(ElementT) - 1 - i] = (uint8_t)tmp;
        }
        ElementT value = 0;
        for(int i = 0; i < sizeof(ElementT); ++i) {
            value = (value << 8) | bytes[i];
        }
        *iterator++ = value;
    } while( iterator < BufferEnd - 1 );

Exit:
    *iterator = 0x0; /* Terminating Zero */
    return iterator;
}

#endif /* __INCLUDE_GUARD__COMMON_H */
