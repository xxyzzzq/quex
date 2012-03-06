/* -*- C++ -*- vim: set syntax=cpp:
 *
 * (C) 2005-2010 Frank-Rene Schaefer                                                */
#ifndef    __QUEX_G_DRAIN_TYPE
#   error "__QUEX_G_DRAIN_TYPE has not been defined."
#endif
#ifndef    __QUEX_G_DRAIN_NAME
#   error "__QUEX_G_DRAIN_NAME has not been defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(unicode, __QUEX_G_DRAIN_NAME)(const size_t                BytesPerCharacter, 
                                                      const void**                source_pp, 
                                                      const void*                 SourceEnd, 
                                                      __QUEX_G_DRAIN_TYPE**       drain_pp, 
                                                      const __QUEX_G_DRAIN_TYPE*  DrainEnd)
{
    switch( BytesPerCharacter ) {
    case 1:   
        __QUEX_CONVERTER_STRING(utf8, __QUEX_G_DRAIN_NAME)((const uint8_t**)source_pp, 
                                                           (const uint8_t*)SourceEnd, 
                                                           drain_pp, DrainEnd); 
        break;
    case 2:   
        __QUEX_CONVERTER_STRING(utf16, __QUEX_G_DRAIN_NAME)((const uint16_t**)source_pp, 
                                                            (const uint16_t*)SourceEnd, 
                                                            drain_pp, DrainEnd); 
        break;
    default:  
        __QUEX_CONVERTER_STRING(utf32, __QUEX_G_DRAIN_NAME)((const uint32_t**)source_pp, 
                                                            (const uint32_t*)SourceEnd, 
                                                            drain_pp, DrainEnd); 
        break;
    }
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
    /* A function based on basic_string<Character> cannot exist at this point. 
     * Otherwise, there would be a dependency on 'QUEX_TYPE_CHARACTER' and there-
     * fore a dependency on the particular analyzer. This cannot be in components
     * of 'quex_universal'.                                                  */
#endif

#undef  __QUEX_G_DRAIN_NAME         
#undef  __QUEX_G_DRAIN_TYPE 

