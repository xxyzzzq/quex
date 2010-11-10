/* (C) 2010 Frank-Rene Schaefer */
QUEX_NAMESPACE_MAIN_OPEN

#ifndef    __QUEX_TO
#    error "__QUEX_TO is not defined."
#endif
#ifndef    __QUEX_TYPE_DRAIN
#    error "__QUEX_TYPE_DRAIN is not defined."
#endif

#define __QUEX_CONVERTER_MY_CHAR   __QUEX_CONVERTER_CHAR(__QUEX_FROM, __QUEX_TO)        
#define __QUEX_CONVERTER_MY_STRING __QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)        

QUEX_INLINE void
__QUEX_CONVERTER_MY_STRING(const QUEX_TYPE_CHARACTER**  source_pp, const QUEX_TYPE_CHARACTER*   SourceEnd, 
                           __QUEX_TYPE_DRAIN**          drain_pp,  const __QUEX_TYPE_DRAIN*     DrainEnd)
{
    const QUEX_TYPE_CHARACTER*  source_iterator; 
    __QUEX_TYPE_DRAIN*          drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd - drain_iterator < (ptrdiff_t)4 ) break;
        __QUEX_CONVERTER_MY_CHAR(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_MY_STRING(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*            source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*            source_end      = source_iterator + Source.length();
    __QUEX_TYPE_DRAIN                     drain[8];
    __QUEX_TYPE_DRAIN*                    drain_iterator = 0;
    std::basic_string<__QUEX_TYPE_DRAIN>  result;

    while( source_iterator != source_end ) {
        drain_iterator = drain;
        __QUEX_CONVERTER_MY_CHAR(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  (QUEX_TYPE_CHARACTER*)Source.c_str());
        __quex_assert(source_iterator <= source_end);
        result.append((__QUEX_TYPE_DRAIN*)drain, (size_t)(drain_iterator - drain));
    }
    return result;
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_CONVERTER_MY_CHAR 
#undef __QUEX_CONVERTER_MY_STRING 
