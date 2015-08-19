/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY              */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I

#include <quex/code_base/definitions>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/buffer/Buffer>

#define QUEX_CAST_FILLER(FILLER) ((QUEX_NAME(BufferFiller_Converter)*)FILLER)

QUEX_NAMESPACE_MAIN_OPEN


    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_NAME(buffer_lexeme_start_pointer_get)(QUEX_TYPE_ANALYZER* me) 
    { return me->buffer._lexeme_start_p; }

    QUEX_INLINE void
    QUEX_NAME(buffer_input_pointer_set)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* Adr)
    { me->buffer._input_p = Adr; }

#   ifndef __QUEX_OPTION_PLAIN_C

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_lexeme_start_pointer_get)() 
    { return QUEX_NAME(buffer_lexeme_start_pointer_get)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_input_pointer_set)(QUEX_TYPE_CHARACTER* Adr)
    { QUEX_NAME(buffer_input_pointer_set)(this, Adr); }

#   endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef QUEX_CAST_FILLER

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I */

