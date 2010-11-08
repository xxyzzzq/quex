/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */
#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

/* Converter Functions: ____________________________________________________________________
 *
 *   $$CODEC$$_to_utf8(...)         -- character to utf8
 *   $$CODEC$$_to_utf8_string(...)  -- string to utf8
 *   $$CODEC$$_to_utf8_string(C++)  -- C++ string to utf8 (std::string)
 *
 *   $$CODEC$$_to_wchar(...)        -- character to utf8
 *   $$CODEC$$_to_wstring(...)      -- string to utf8
 *   $$CODEC$$_to_wstring(C++)      -- C++ string to utf8 (std::wstring)
 *__________________________________________________________________________________________*/

#ifndef   __QUEX_CONVERTER_FROM
#   error "__QUEX_CONVERTER_FROM must be defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8_string)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                            const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                            uint8_t**                    drain_pp,  
                                                            const uint8_t*               DrainEnd)
{
    const QUEX_TYPE_CHARACTER*  source_iterator; 
    uint8_t*                    drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd - drain_iterator < (ptrdiff_t)4 ) break;
        __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::string
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8_string)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*    source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*    source_end      = source_iterator + Source.length();
    uint8_t                       drain[8];
    uint8_t*                      drain_iterator = 0;
    std::string                   result;

    while( source_iterator != source_end ) {
        drain_iterator = drain;
        __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  (QUEX_TYPE_CHARACTER*)Source.c_str());
        __quex_assert(source_iterator <= source_end);
        result.append((char*)drain, (drain_iterator - drain));
    }
    return result;
}
#endif

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                        const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                        wchar_t**                    drain_pp,  
                                                        const wchar_t*               DrainEnd)
{
    const QUEX_TYPE_CHARACTER*  source_iterator; 
    wchar_t*                    drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd <= drain_iterator ) break;
        __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wchar)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::wstring
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wstring)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*    source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*    source_end      = source_iterator + Source.length();
    wchar_t                       drain[8];
    wchar_t*                      drain_iterator = 0;
    std::wstring                  result;

    while( source_iterator != source_end ) {
        drain_iterator = drain;
        __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, wchar)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  (QUEX_TYPE_CHARACTER*)Source.c_str());
        __quex_assert(source_iterator <= source_end);
        result.append((wchar_t*)drain, (drain_iterator - drain));
    }
    return result;
}
#endif

#endif /* not __QUEX_OPTION_WCHAR_T_DISABLED */

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_CONVERTER_FROM
