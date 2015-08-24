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



QUEX_NAMESPACE_MAIN_CLOSE

#undef QUEX_CAST_FILLER

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I */

