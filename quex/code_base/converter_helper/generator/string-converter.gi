/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: 
 *
 * Generate string converter functions which convert a string from one 
 * character codec into another. The conversion is implemented by means
 * of a character converter function given by:
 *
 *            __QUEX_CONVERTER_CHAR(FROM, TO)(in, out); 
 *
 * which converts only a single character. The converter function must
 * be defined before the inclusion of this file.
 *
 * PARAMETERS (must be defined macros):
 *
 *      __QUEX_FROM            -- Name of the source character encoding.
 *      __QUEX_FROM_TYPE       -- Type of characters that carry the source.
 *      __QUEX_FROM_MAX_LENGTH -- [1/sizeof(__QUEX_FROM_TYPE)]
 *                                Maximum character size in coding in terms
 *                                of a code element (== sizeof(__QUEX_FROM_TYPE)). 
 *                                This is important to maintain a safety margin.
 *      __QUEX_TO              -- Name of the target encoding.
 *      __QUEX_TO_TYPE         -- Type of characters that carry the drain.            
 *
 * (C) 2010-2012 Frank-Rene Schaefer 
 * ABSOLUTELY NO WARRANTY                                                    */

#if   ! defined(__QUEX_FROM)
#   error "__QUEX_FROM must be defined."
#elif __QUEX_FROM   == utf8
#    define __QUEX_FROM_MAX_LENGTH 4
#elif __QUEX_FROM == utf16
#    define __QUEX_FROM_MAX_LENGTH 2
#elif __QUEX_FROM == utf16
#    define __QUEX_FROM_MAX_LENGTH 1
#elif ! defined(__QUEX_FROM_MAX_LENGTH)
#    error "For codecs other than utf8, utf16, or utf32 __QUEX_FROM_MAX_LENGTH must be defined."
#endif
#if   ! defined(__QUEX_FROM_TYPE)
#   error "__QUEX_FROM_TYPE must be defined."
#elif ! defined(__QUEX_TO_TYPE)
#   error "__QUEX_TO_TYPE must be defined."
#elif ! defined(__QUEX_TO)
#   error "__QUEX_TO must be defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_FROM_TYPE**  source_pp, 
                                                const __QUEX_FROM_TYPE*   SourceEnd, 
                                                __QUEX_TO_TYPE**          drain_pp,  
                                                const __QUEX_TO_TYPE*     DrainEnd)
{
    const __QUEX_FROM_TYPE*  source_iterator; 
    __QUEX_TO_TYPE*          drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd - drain_iterator < (ptrdiff_t)__QUEX_FROM_MAX_LENGTH ) break;
        __QUEX_CONVERTER_CHAR(__QUEX_FROM, __QUEX_TO)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TO_TYPE>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_FROM_TYPE>& Source)
{
    const __QUEX_FROM_TYPE*            source_iterator = (__QUEX_FROM_TYPE*)Source.c_str();
    const __QUEX_FROM_TYPE*            source_end      = source_iterator + Source.length();
    __QUEX_TO_TYPE                     drain[__QUEX_FROM_MAX_LENGTH + 1];
    __QUEX_TO_TYPE*                    drain_iterator  = 0;
    std::basic_string<__QUEX_TO_TYPE>  result;

    while( source_iterator != source_end ) {
        drain_iterator = drain;
        __QUEX_CONVERTER_CHAR(__QUEX_FROM, __QUEX_TO)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  (__QUEX_FROM_TYPE*)Source.c_str());
        __quex_assert(source_iterator <= source_end);
        result.append((__QUEX_TO_TYPE*)drain, (size_t)(drain_iterator - drain));
    }
    return result;
}
#endif

#undef __QUEX_FROM_MAX_LENGTH
#undef __QUEX_TO
#undef __QUEX_TO_TYPE
