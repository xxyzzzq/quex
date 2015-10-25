/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I

#include    <quex/code_base/definitions>
#include    <quex/code_base/buffer/Buffer>
#include    <quex/code_base/buffer/filler/BufferFiller>
#include    <quex/code_base/buffer/asserts>
#ifdef      QUEX_OPTION_INCLUDE_STACK
#   include <quex/code_base/analyzer/struct/include-stack>
#endif

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

    /* NOTE: 'reload_forward()' needs to be implemented for each mode, because
     *       addresses related to acceptance positions need to be adapted. This
     *       is not the case for 'reload_backward()'. In no case of backward
     *       reloading, there are important addresses to keep track.            */
    QUEX_INLINE void 
    QUEX_NAME(buffer_reload_backward)(QUEX_NAME(Buffer)* buffer)
    {
        __quex_assert(buffer);
        __quex_assert(buffer->filler);

        if( buffer->on_buffer_content_change ) {
            /* In contrast to 'reload forward', a reload backward is very well 
             * conceivable, even if end of file pointer != 0x0.              */
            buffer->on_buffer_content_change(buffer->_memory._front, 
                                             buffer->_input.end_p);
        }

        QUEX_NAME(Buffer_load_backward)(buffer);
        
        /* NO ADAPTIONS OF POST-CONTEXT POSITIONS !
         *
         * Backward lexing happens in two cases:
         *
         *  (1) When checking for a pre-condition. In this case, no dedicated
         *  acceptance is involved. No acceptance positions are considered.
         *
         *  (2) When tracing back to get the end of a core pattern in
         *  pseudo-ambigous post conditions. Then, no acceptance positions are
         *  involved, because the start of the lexeme shall not drop before the
         *  begin of the buffer and the end of the core pattern, is of course,
         *  after the start of the lexeme. => there will be no reload
         *  backwards.                                                       */
    }

    QUEX_INLINE void 
    QUEX_NAME(buffer_reload_forward)(QUEX_NAME(Buffer)*    buffer, 
                                     QUEX_TYPE_CHARACTER** position_register,
                                     const size_t          PositionRegisterN)
    {
        QUEX_TYPE_CHARACTER**     iterator           = 0x0;
        QUEX_TYPE_CHARACTER**     End                = position_register + (ptrdiff_t)PositionRegisterN;
        QUEX_TYPE_STREAM_POSITION previous_character_index_begin;
        ptrdiff_t                 offset;

        if( buffer->input.end_p ) {
            return;
        }
        if( buffer->on_buffer_content_change ) {
            /* If the end of file pointer is set, the reload will not be
             * initiated, and the buffer remains as is. No reload happens,
             * see above.  => HERE: end of content = end of buffer.          */
            buffer->on_buffer_content_change(buffer->_memory._front, 
                                             buffer->_memory._back);
        }

        previous_character_index_begin = QUEX_NAME(Buffer_input_character_index_begin)(buffer);

        QUEX_NAME(Buffer_load_forward)(buffer);

        offset = (ptrdiff_t)(  QUEX_NAME(Buffer_input_character_index_begin)(buffer) 
                             - previous_character_index_begin);

        for(iterator = position_register; iterator != End; ++iterator) {
            *iterator = (*iterator - &buffer->_memory._front[1]) >= offset ? *iterator - offset : 0;
        }
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I */
