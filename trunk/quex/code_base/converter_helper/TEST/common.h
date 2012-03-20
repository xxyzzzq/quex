/* Configure this header by defining one of:
 *
 *    TEST_UTF8, TEST_UTF16, TEST_UNICODE, TEST_CODEC
 *                                                      */
#ifndef __INCLUDE_GUARD__COMMON_H
#define __INCLUDE_GUARD__COMMON_H

#define QUEX_NAMESPACE_MAIN        Tester
#define QUEX_NAMESPACE_MAIN_OPEN   namespace Tester {
#define QUEX_NAMESPACE_MAIN_CLOSE  }
#define QUEX_NAMESPACE_TOKEN_OPEN  namespace TesterToken {
#define QUEX_NAMESPACE_TOKEN_CLOSE }

#define ____QUEX_CONVERTER_CHAR(FROM, TO)    TesterToken_ ## FROM ## _to_ ## TO ## _character
#define QUEX_CONVERTER_CHAR(FROM, TO)        ____QUEX_CONVERTER_CHAR(FROM, TO)
#define QUEX_CONVERTER_CHAR_DEF(FROM, TO)    ____QUEX_CONVERTER_CHAR(FROM, TO)
#define ____QUEX_CONVERTER_STRING(FROM, TO)  TesterToken_ ## FROM ## _to_ ## TO
#define QUEX_CONVERTER_STRING(FROM, TO)      ____QUEX_CONVERTER_STRING(FROM, TO)
#define QUEX_CONVERTER_STRING_DEF(FROM, TO)  ____QUEX_CONVERTER_STRING(FROM, TO)

#define QUEX_SETTING_CHAR_CODEC    8
#define QUEX_SETTING_WCHAR_CODEC   32

#include <quex/code_base/converter_helper/from-utf8.i>
#include <quex/code_base/converter_helper/from-utf16.i>
#include <quex/code_base/converter_helper/from-utf32.i>

using namespace std;

#define ____MYSTRING(X) #X
#define __MYSTRING(X) ____MYSTRING(X)


#endif /* __INCLUDE_GUARD__COMMON_H */
