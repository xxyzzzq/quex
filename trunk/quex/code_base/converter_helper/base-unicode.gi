/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_TO)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                            const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                            __QUEX_TYPE_DRAIN**          drain_pp, 
                                            const __QUEX_TYPE_DRAIN*     DrainEnd)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1:   
        __QUEX_CONVERTER_STRING(utf8, __QUEX_TO)((uint8_t**)input_pp, (uint8_t*)SourceEnd, 
                                                 drain_pp,            DrainEnd); 
        break;
    case 2:   
        __QUEX_CONVERTER_STRING(utf16, __QUEX_TO)((uint16_t**)input_pp, (uint16_t*)SourceEnd, 
                                                  drain_pp,             DrainEnd); 
        break;
    default:  
        __QUEX_CONVERTER_STRING(utf32, __QUEX_TO)((uint32_t**)input_pp, (uint32_t*)SourceEnd, 
                                                  drain_pp,             DrainEnd); 
        break;
    }
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(unicode, __QUEX_TO)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1:   
        std::basic_string<uint8_t>  tmp((uint8_t*)Source.c_str());
        return __QUEX_CONVERTER_STRING(utf8, __QUEX_TO)(tmp); 
    case 2:   
        std::basic_string<uint16_t>  tmp((uint16_t*)Source.c_str());
        return __QUEX_CONVERTER_STRING(utf16, __QUEX_TO)(tmp);
    default:  
        std::basic_string<uint32_t>  tmp((uint32_t*)Source.c_str());
        return __QUEX_CONVERTER_STRING(utf32, __QUEX_TO)(tmp); 
    }
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef  __QUEX_TO         
#undef  __QUEX_TYPE_DRAIN 
