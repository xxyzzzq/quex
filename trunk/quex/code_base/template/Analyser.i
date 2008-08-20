/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __INCLUDE_GUARD__QUEX__CODE_BASE__ANALYSER_MINIMAL_I__
#define __INCLUDE_GUARD__QUEX__CODE_BASE__ANALYSER_MINIMAL_I__

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller.i>

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

    QUEX_INLINE void
    QuexAnalyser_init(QuexAnalyser* me,
                      QUEX_ANALYSER_FUNCTION_TYPE AnalyserFunction,
                      const char* IANA_InputCodingName)
    {
        QuexBuffer_instantiate(&me->buffer, Size, 
                               IANA_InputCodingName, IANA_InputCodingName == 0 ? QUEX_PLAIN : QUEX_ICONV,
                               65536, 65536);
        me->current_analyser_function = AnalyserFunction;

        /* Double check that everything is setup propperly. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        __quex_assert(me->buffer._input_p == me->buffer._memory._front + 1);
    }

    /* NOTE: 'reload_forward()' needs to be implemented for each mode, because
     *       addresses related to acceptance positions need to be adapted. This
     *       is not the case for 'reload_backward()'. In no case of backward
     *       reloading, there are important addresses to keep track. */
    QUEX_INLINE bool 
    QuexAnalyser_buffer_reload_backward(QuexBuffer* buffer)
    {
        if( buffer->filler == 0x0 ) return false;

        const size_t LoadedByteN = QuexBufferFiller_load_backward(buffer);
        if( LoadedByteN == 0 ) return false;
        
        /* Backward lexing happens in two cases:
         *
         *  (1) When checking for a pre-condition. In this case, no dedicated acceptance
         *      is involved. No acceptance positions are considered.
         *  (2) When tracing back to get the end of a core pattern in pseudo-ambigous
         *      post conditions. Then, no acceptance positions are involved, because
         *      the start of the lexeme shall not drop before the begin of the buffer 
         *      and the end of the core pattern, is of course, after the start of the 
         *      lexeme. => there will be no reload backwards. */
        return true;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex 
#endif

#endif /* __INCLUDE_GUARD__QUEX__CODE_BASE__ANALYSER_MINIMAL_I__ */
