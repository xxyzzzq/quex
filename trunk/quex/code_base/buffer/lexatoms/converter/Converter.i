/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__CONVERTER_I
#define  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__CONVERTER_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/lexatoms/converter/Converter>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE bool
QUEX_NAME(Converter_construct)(QUEX_NAME(Converter)* me,
                               const char*  FromCodec, const char* ToCodec,
                               bool         (*open)(struct QUEX_NAME(Converter_tag)*, 
                                                    const char* FromCodec, const char* ToCodec),  
                               E_LoadResult (*convert)(QUEX_NAME(Converter)*, 
                                                       uint8_t**             source, const uint8_t*             SourceEnd, 
                                                       QUEX_TYPE_LEXATOM** drain,  const QUEX_TYPE_LEXATOM* DrainEnd),
                               void         (*delete_self)(QUEX_NAME(Converter)*),
                               ptrdiff_t    (*stomach_byte_n)(QUEX_NAME(Converter)*),
                               void         (*stomach_clear)(QUEX_NAME(Converter)*))
/* RETURNS: true  -- construction succesful
 *          false -- else.                                                   */
{
    me->convert            = convert;
    me->stomach_byte_n     = stomach_byte_n;
    me->stomach_clear      = stomach_clear;
    me->delete_self        = delete_self;

    me->virginity_f        = true;
    me->byte_n_per_lexatom = -1;     /* No fixed ratio 'byte_n/lexatom' */
    me->ownership          = E_Ownership_EXTERNAL;

    /* Opens internally a conversion handle for the conversion from 'FromCodec'
     * to 'ToCodec'. Pass '0x0' as 'ToCodec' in order to indicate a conversion
     * to unicode of size sizeof(QUEX_TYPE_LEXATOM). 
     *
     * It is the task of the particular implementation to provide the 'ToCodec'
     * which is appropriate for sizeof(QUEX_TYPE_LEXATOM), i.e.  ASCII, UCS2,
     * UCS4.                                                                 */

    return open(me, FromCodec, ToCodec);
}

QUEX_NAMESPACE_MAIN_CLOSE

#endif /*  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__CONVERTER__CONVERTER_I */
