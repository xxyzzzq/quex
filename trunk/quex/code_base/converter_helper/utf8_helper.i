#ifndef __QUEX_INCLUDE_GUARD__UTF8_HELPER_I
#define __QUEX_INCLUDE_GUARD__UTF8_HELPER_I
/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */

QUEX_NAMESPACE_MAIN_OPEN

#if ! define(__QUEX_OPTION_WCHAR_T_DISABLED)
QUEX_INLINE void
/* DrainEnd pointer is not returned, since the increment is always '1' */
QUEX_NAME(utf8_to_wchar_t)(QUEX_TYPE_CHARACTER** input_pp, wchar_t** output_pp)
{
    QUEX_TYPE_CHARACTER*  iterator = input_pp;

    if( (*iterator & 0x80) == 0 ) {
        /* Header: 0xxx.xxxx */
        **output_pp = (wchar_t)*iterator;
    }
    else if( *iterator < 0xE0 ) { /* ... max: 1101.1111 --> 0xDF, next: 0xE0 */
        /*    110x.xxxx 10yy.yyyy 
         * => 0000.0xxx:xxyy.yyyy  */
        **output_pp =   (( ((wchar_t)*(iterator++)) & 0x1F ) << 6) 
                      | (( ((wchar_t)*(iterator++)) & 0x3F )     );
    }
    else if( *iterator < 0xF0 ) { /* ... max: 1110.1111 --> 0xEF, next: 0xF0 */
        /*    1110.xxxx 10yy.yyyy 10zz.zzzz
         * => xxxx.yyyy:yyzz.zzzz           */
        **output_pp =   (( ((wchar_t)*(iterator++)) & 0x0F ) << 12) 
                      | (( ((wchar_t)*(iterator++)) & 0x3F ) << 6 ) 
                      | (( ((wchar_t)*(iterator++)) & 0x3F )      );
    }
    else {
        /* Unicode standard defines only chars until 0x10ffff, so max(len(utf8char)) == 4.
         *
         * NO CHECK: if( *iterator < 0xF8 ) { ... max: 1111.0111 --> 0xF7, next: 0xF8 
         *
         *    1111.0uuu 10xx.xxxx 10yy.yyyy 10zz.zzzz
         * => 000u.uuxx:xxxx.yyyy:yyzz.zzzz           */
        **output_pp =   (( ((wchar_t)*(iterator + 0)) & 0x07 ) << 18) 
                      | (( ((wchar_t)*(iterator + 1)) & 0x3F ) << 12) 
                      | (( ((wchar_t)*(iterator + 2)) & 0x3F ) << 6 ) 
                      | (( ((wchar_t)*(iterator + 3)) & 0x3F )      );
    }
    ++(*output_pp);
    *input_pp = iterator;
}

QUEX_INLINE void
QUEX_NAME(utf8_to_wchar_string)(const QUEX_TYPE_CHARACTER* Source, size_t SourceSize,
                                wchar_t**       Drain, size_t  DrainSize);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::wstring
QUEX_NAME(utf8_to_wstring)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
#endif 

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__UTF8_HELPER_I */
