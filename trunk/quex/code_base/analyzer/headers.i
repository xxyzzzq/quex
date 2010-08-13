/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                      */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__HEADERS_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__HEADERS_I

#include    <quex/code_base/aux-string.i>
#include    <quex/code_base/unicode.i>

/* Token sending happens only via macros, for flexibility. */
#include    <quex/code_base/analyzer/member/token-receiving.i>
#include    <quex/code_base/analyzer/member/mode-handling.i>
#include    <quex/code_base/analyzer/member/buffer-access.i>
#include    <quex/code_base/analyzer/member/misc.i>
#include    <quex/code_base/analyzer/member/constructor.i>

#include    <quex/code_base/analyzer/member/basic.i>
#include    <quex/code_base/MemoryManager.i>
#include    <quex/code_base/analyzer/Mode.i>
#include    <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#ifdef      __QUEX_OPTION_COUNTER
#include    <quex/code_base/analyzer/counter/Base.i>
#endif
#ifdef      QUEX_OPTION_INCLUDE_STACK
#   include <quex/code_base/analyzer/member/include-stack.i>
#endif
#ifdef      QUEX_OPTION_STRING_ACCUMULATOR
#   include <quex/code_base/analyzer/Accumulator.i>
#endif
#ifdef      QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue.i>
#endif
#ifdef      QUEX_OPTION_POST_CATEGORIZER
#   include <quex/code_base/analyzer/PostCategorizer.i>
#endif
#ifdef      __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
#   include <quex/code_base/analyzer/IndentationStack.i>
#endif

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__HEADERS_I */
