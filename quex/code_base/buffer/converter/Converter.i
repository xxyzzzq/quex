/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__CONVERTER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__CONVERTER_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/converter/Converter>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(Converter_construct)(QUEX_NAME(Converter)* me,
                    void    (*open)(struct QUEX_NAME(Converter_tag)*, 
                                    const char* FromCodingName, const char* ToCodingName),  
                    bool    (*convert)(struct QUEX_NAME(Converter_tag)*, 
                                       uint8_t**             source, const uint8_t*             SourceEnd, 
                                       QUEX_TYPE_CHARACTER** drain,  const QUEX_TYPE_CHARACTER* DrainEnd),
                    void    (*delete_self)(struct QUEX_NAME(Converter_tag)*),
                    void    (*on_conversion_discontinuity)(struct QUEX_NAME(Converter_tag)*))
{
    me->open                        = open;
    me->convert                     = convert;
    me->on_conversion_discontinuity = on_conversion_discontinuity;
    me->delete_self                 = delete_self;

    me->virginity_f                 = true;
    me->dynamic_character_size_f    = true;
    me->ownership                   = E_Ownership_EXTERNAL;
}
QUEX_INLINE void
QUEX_NAME(Converter_delete)(QUEX_NAME(Converter)** me)
{
    if     ( ! *me )                                            return;
    else if( (*me)->ownership != E_Ownership_LEXICAL_ANALYZER ) return;
    else if( (*me)->delete_self )                               (*me)->delete_self(*me);
    *me = (QUEX_NAME(Converter)*)0;
}

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__CONVERTER_I */
