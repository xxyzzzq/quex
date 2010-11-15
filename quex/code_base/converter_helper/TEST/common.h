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

#define QUEX_SETTING_CHAR_CODEC    8
#define QUEX_SETTING_WCHAR_CODEC   32

#include <quex/code_base/converter_helper/utf8.i>
#include <quex/code_base/converter_helper/utf16.i>
#include <quex/code_base/converter_helper/utf32.i>

using namespace std;

#define ____MYSTRING(X) #X
#define __MYSTRING(X) ____MYSTRING(X)


#endif /* __INCLUDE_GUARD__COMMON_H */
