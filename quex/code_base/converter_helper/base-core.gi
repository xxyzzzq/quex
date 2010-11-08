/* (C) 2010 Frank-Rene Schaefer */
QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, __QUEX_CONVERTER_TO)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                                                    const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                                    __QUEX_TYPE_DRAIN**          drain_pp,  
                                                                    const __QUEX_TYPE_DRAIN*     DrainEnd)
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
        __QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, utf8)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::base_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_HELPER(__QUEX_CONVERTER_FROM, __QUEX_TYPE_DRAIN)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*           source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*           source_end      = source_iterator + Source.length();
    __QUEX_TYPE_DRAIN                    drain[8];
    __QUEX_TYPE_DRAIN*                   drain_iterator = 0;
    std::base_string<__QUEX_TYPE_DRAIN>  result;

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

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_CONVERTER_TO
#undef __QUEX_TYPE_DRAIN

