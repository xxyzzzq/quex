/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef    __QUEX_UNI_TYPE_DRAIN
#   error "__QUEX_UNI_TYPE_DRAIN has not been defined."
#endif
#ifndef    __QUEX_UNI_TO
#   error "__QUEX_UNI_TO has not been defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_UNI_TO)(const size_t                   BytesPerCharacter, 
                                                const void**                   source_pp, 
                                                const void*                    SourceEnd, 
                                                __QUEX_UNI_TYPE_DRAIN**        drain_pp, 
                                                const __QUEX_UNI_TYPE_DRAIN*   DrainEnd)
{
    switch( BytesPerCharacter ) {
    case 1:   
        __QUEX_CONVERTER_STRING(utf8, __QUEX_UNI_TO)((const uint8_t**)source_pp, 
                                                     (const uint8_t*)SourceEnd, 
                                                     drain_pp, DrainEnd); 
        break;
    case 2:   
        __QUEX_CONVERTER_STRING(utf16, __QUEX_UNI_TO)((const uint16_t**)source_pp, 
                                                      (const uint16_t*)SourceEnd, 
                                                      drain_pp, DrainEnd); 
        break;
    default:  
        __QUEX_CONVERTER_STRING(utf32, __QUEX_UNI_TO)((const uint32_t**)source_pp, 
                                                      (const uint32_t*)SourceEnd, 
                                                      drain_pp, DrainEnd); 
        break;
    }
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_UNI_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(unicode, __QUEX_UNI_TO)(const size_t BytesPerCharacter, 
                                                const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    switch( BytesPerCharacter ) {
    case 1: {
                std::basic_string<uint8_t>  tmp((const uint8_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf8, __QUEX_UNI_TO)(tmp); 
        }
    case 2: {
                std::basic_string<uint16_t>  tmp((const uint16_t*)Source.c_str());
                return __QUEX_CONVERTER_STRING(utf16, __QUEX_UNI_TO)(tmp);
        }
    default: { 
                 std::basic_string<uint32_t>  tmp((const uint32_t*)Source.c_str());
                 return __QUEX_CONVERTER_STRING(utf32, __QUEX_UNI_TO)(tmp); 
        }
    }
}
#endif

#undef  __QUEX_UNI_TO         
#undef  __QUEX_UNI_TYPE_DRAIN 

