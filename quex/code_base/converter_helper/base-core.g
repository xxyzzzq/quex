/* (C) 2010 Frank-Rene Schaefer */
#ifndef __QUEX_FROM
#   error "__QUEX_FROM must be defined."
#endif
#ifndef __QUEX_TO
#   error "__QUEX_TO must be defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

#define __QUEX_CONVERTER_MY_STRING \
        __QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)        

QUEX_INLINE void
__QUEX_CONVERTER_MY_STRING(const QUEX_TYPE_CHARACTER**  source_pp, const QUEX_TYPE_CHARACTER*   SourceEnd, 
                           __QUEX_TYPE_DRAIN**          drain_pp,  const __QUEX_TYPE_DRAIN*     DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_MY_STRING(const std::basic_string<QUEX_TYPE_CHARACTER>& Source);
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_CONVERTER_MY_STRING
