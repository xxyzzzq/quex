/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE:
 * 
 * (C) 2005-2010 Frank-Rene Schaefer                                                
 * ABSOLUTELY NO WARRANTY                                                    */

#if     defined(__QUEX_FROM)
#   error "__QUEX_FROM must NOT be defined. Source name is 'unicode' for this header."
#elif   defined(__QUEX_FROM_TYPE)
#   error "__QUEX_FROM_TYPE must NOT be defined. Source type is QUEX_TYPE_CHARACTER."
#elif ! defined(__QUEX_TO_TYPE)
#   error "__QUEX_TO_TYPE must be defined."
#elif ! defined(__QUEX_TO)
#   error "__QUEX_TO must be defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_TO)(const QUEX_TYPE_CHARACTER** source_pp, 
                                           const QUEX_TYPE_CHARACTER*  SourceEnd, 
                                           __QUEX_TO_TYPE**         drain_pp, 
                                           const __QUEX_TO_TYPE*    DrainEnd)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1:   
        __QUEX_CONVERTER_STRING(utf8, __QUEX_TO)((const uint8_t**)source_pp, 
                                                 (const uint8_t*)SourceEnd, 
                                                 drain_pp, DrainEnd); 
        break;
    case 2:   
        __QUEX_CONVERTER_STRING(utf16, __QUEX_TO)((const uint16_t**)source_pp, 
                                                  (const uint16_t*)SourceEnd, 
                                                  drain_pp, DrainEnd); 
        break;
    default:  
        __QUEX_CONVERTER_STRING(utf32, __QUEX_TO)((const uint32_t**)source_pp, 
                                                  (const uint32_t*)SourceEnd, 
                                                  drain_pp, DrainEnd); 
        break;
    }
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TO_TYPE>
__QUEX_CONVERTER_STRING(unicode, __QUEX_TO)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
    case 1: {
                std::basic_string<uint8_t>  tmp((const uint8_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf8, __QUEX_TO)(tmp); 
            }
    case 2: {
                std::basic_string<uint16_t>  tmp((const uint16_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf16, __QUEX_TO)(tmp);
            }
    default: { 
                 std::basic_string<uint32_t>  tmp((const uint32_t*)Source.c_str());
                 return __QUEX_CONVERTER_STRING(utf32, __QUEX_TO)(tmp); 
             }
    }
}
#endif

#undef  __QUEX_TO         
#undef  __QUEX_TO_TYPE 

