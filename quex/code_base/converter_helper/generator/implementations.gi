/* PURPOSE:
 * 
 * Generate function implementations for all string converters FROM 
 * a given codec:
 *
 *        __QUEX_CONVERTER_STRING(FROM, utf8)(...)
 *        __QUEX_CONVERTER_STRING(FROM, utf16)(...)
 *        __QUEX_CONVERTER_STRING(FROM, utf32)(...)
 *        __QUEX_CONVERTER_STRING(FROM, char)(...)
 *        __QUEX_CONVERTER_STRING(FROM, wchar_t)(...)
 *
 * It is Assumed that the character converters for each function are 
 * available!
 *
 * PARAMETERS:
 *
 *   __QUEX_FROM        Name of the input character codec.
 *   __QUEX_FROM_TYPE   Type of the input characters.
 *
 * (C) 2012 Frank-Rene Schaefer; ABSOLUTELY NO WARRANTY                      */ 
#if ! defined(__QUEX_FROM)
#    error "__QUEX_FROM must be defined!"
#elif ! defined(__QUEX_FROM_TYPE)
#    error "__QUEX_FROM_TYPE must be defined!"
#endif

#define  __QUEX_TO         utf8
#define  __QUEX_TO_TYPE    uint8_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>
#define  __QUEX_TO         utf16
#define  __QUEX_TO_TYPE    uint16_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>
#define  __QUEX_TO         utf32
#define  __QUEX_TO_TYPE    uint32_t
#include <quex/code_base/converter_helper/generator/string-converter.gi>
#define  __QUEX_TO         char
#define  __QUEX_TO_TYPE    char
#include <quex/code_base/converter_helper/generator/string-converter.gi>

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
#   define  __QUEX_TO         wchar_t
#   define  __QUEX_TO_TYPE    wchar_t
#   include <quex/code_base/converter_helper/generator/string-converter.gi>
#endif

