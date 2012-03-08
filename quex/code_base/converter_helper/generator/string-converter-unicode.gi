/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE:
 * 
 * This file generates a string converter from unicode to a given target codec.
 * It does so by 'routing', that is it calls the correspondent string converter
 * from the existing bank of converters. It can handle only UNICODE source 
 * codings.
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                
 * ABSOLUTELY NO WARRANTY                                                    */
#ifndef    __QUEX_FROM_TYPE 
#   error "__QUEX_FROM_TYPE must be defined."
#ifndef    __QUEX_TO_TYPE
#   error "__QUEX_TO_TYPE must be defined."
#endif
#ifndef    __QUEX_TO
#   error "__QUEX_TO must be defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_TO)(const __QUEX_FROM_TYPE** source_pp, 
                                            const __QUEX_FROM_TYPE*  SourceEnd, 
                                            __QUEX_TO_TYPE**         drain_pp, 
                                            const __QUEX_TO_TYPE*    DrainEnd)
{
    switch( sizeof(__QUEX_FROM_TYPE) ) {
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
__QUEX_CONVERTER_STRING(unicode, __QUEX_UNI_TO)(const std::basic_string<__QUEX_FROM_TYPE>& Source)
{
    switch( sizeof(__QUEX_FROM_TYPE) ) {
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

