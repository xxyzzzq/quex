/* (C) 2010 Frank-Rene Schaefer */
#ifndef __QUEX_G_SOURCE_NAME
#   error "__QUEX_G_SOURCE_NAME must be defined."
#endif
#ifndef __QUEX_TO
#   error "__QUEX_TO must be defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_G_SOURCE_NAME, __QUEX_TO)(const __QUEX_G_SOURCE_TYPE**  source_pp, 
                                                const __QUEX_G_SOURCE_TYPE*   SourceEnd, 
                                                __QUEX_TYPE_DRAIN**         drain_pp,  
                                                const __QUEX_TYPE_DRAIN*    DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(__QUEX_G_SOURCE_NAME, __QUEX_TO)(const std::basic_string<__QUEX_G_SOURCE_TYPE>& Source);
#endif

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_CONVERTER_MY_STRING
