/* (C) 2010 Frank-Rene Schaefer */

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, __QUEX_CONVERTER_TO)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                                    const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                                    __QUEX_TYPE_DRAIN**          drain_pp,  
                                                                    const __QUEX_TYPE_DRAIN*     DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
    QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
    __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, __QUEX_CONVERTER_TO)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_CONVERTER_TO
#undef __QUEX_TYPE_DRAIN
