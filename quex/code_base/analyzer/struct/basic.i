/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I

#include    <quex/code_base/definitions>
#include    <quex/code_base/buffer/Buffer>
#include    <quex/code_base/buffer/BufferFiller>
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
             * conceivable, even if end of file pointer != 0x0.                          */
            buffer->on_buffer_content_change(buffer->_memory._front, 
                                             QUEX_NAME(Buffer_text_end)(buffer));
        }

        (void)QUEX_NAME(BufferFiller_load_backward)(buffer);
        
        /* Backward lexing happens in two cases:
         *
         *  (1) When checking for a pre-condition. In this case, no dedicated acceptance
         *      is involved. No acceptance positions are considered.
         *  (2) When tracing back to get the end of a core pattern in pseudo-ambigous
         *      post conditions. Then, no acceptance positions are involved, because
         *      the start of the lexeme shall not drop before the begin of the buffer 
         *      and the end of the core pattern, is of course, after the start of the 
         *      lexeme. => there will be no reload backwards.                            */
    }

    QUEX_INLINE size_t 
    QUEX_NAME(__buffer_reload_forward_core)(QUEX_NAME(Buffer)*  buffer) 
    {
        size_t loaded_character_n = (size_t)-1;

        __quex_assert(buffer);
        __quex_assert(buffer->filler);
        __quex_assert(! buffer->_memory._end_of_file_p);

        if( buffer->_memory._end_of_file_p ) {
            return 0;
        }

        if( buffer->on_buffer_content_change ) {
            /* If the end of file pointer is set, the reload will not be initiated,
             * and the buffer remains as is. No reload happens, see above. 
             * => HERE: end of content = end of buffer.                             */
            buffer->on_buffer_content_change(buffer->_memory._front, 
                                             buffer->_memory._back);
        }

        loaded_character_n = QUEX_NAME(BufferFiller_load_forward)(buffer);
        return loaded_character_n;
    }

    QUEX_INLINE void 
    QUEX_NAME(buffer_reload_forward)(QUEX_NAME(Buffer)*            buffer, 
                                     QUEX_TYPE_CHARACTER_POSITION* position_register,
                                     const size_t                  PositionRegisterN)
    {
        QUEX_TYPE_CHARACTER_POSITION*  iterator           = 0x0;
        QUEX_TYPE_CHARACTER_POSITION*  End                = position_register + (ptrdiff_t)PositionRegisterN;
        size_t                         loaded_character_n = (size_t)-1;    

        loaded_character_n = QUEX_NAME(__buffer_reload_forward_core)(buffer);

        for(iterator = position_register; iterator != End; ++iterator) {
            /* NOTE: When the post_context_start_position is still undefined the following operation may
             *       underflow. But, do not care, once it is **assigned** to a meaningful value, it won't */
            *iterator -= (ptrdiff_t)loaded_character_n;
        }
    }

    QUEX_INLINE void
    QUEX_NAME(Asserts_construct)(const char* CharacterEncodingName)
    {
#       if      defined(QUEX_OPTION_ASSERTS) \
        && ! defined(QUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED)
        __QUEX_STD_printf(__QUEX_MESSAGE_ASSERTS_INFO);
#       endif

#       if      defined(QUEX_OPTION_ASSERTS) 
        if( QUEX_SETTING_BUFFER_LIMIT_CODE == QUEX_SETTING_PATH_TERMINATION_CODE ) {
            QUEX_ERROR_EXIT("Path termination code (PTC) and buffer limit code (BLC) must be different.\n");
        }
#       endif

#       if  defined(__QUEX_OPTION_ENGINE_RUNNING_ON_CODEC)
        if( CharacterEncodingName ) {
            __QUEX_STD_printf(__QUEX_MESSAGE_CHARACTER_ENCODING_SPECIFIED_WITHOUT_CONVERTER, CharacterEncodingName);
        }
#       endif
    }

    QUEX_INLINE void
    QUEX_NAME(Tokens_construct)(QUEX_TYPE_ANALYZER* me)
    {
#   if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
#       if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
        /* Assume that the user will pass us a constructed token queue */
        QUEX_NAME(TokenQueue_init)(&me->_token_queue, 0, 0x0);
#       else
        QUEX_NAME(TokenQueue_construct)(&me->_token_queue, 
                                        (QUEX_TYPE_TOKEN*)&me->__memory_token_queue,
                                        QUEX_SETTING_TOKEN_QUEUE_SIZE);
#       endif
#   elif defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
        /* Assume that the user will pass us a constructed token */
        me->token = ((QUEX_TYPE_TOKEN)*)0x0;     
#   else
        me->token = &me->__memory_token;     
#       ifdef __QUEX_OPTION_PLAIN_C
        QUEX_NAME_TOKEN(construct)(me->token);
#       endif
#   endif
    }

    QUEX_INLINE void
    QUEX_NAME(Tokens_destruct)(QUEX_TYPE_ANALYZER* me)
    {
        /* Even if the token memory is user managed, the destruction (not the
         * freeing of memory) must happen at this place.                     */
#       ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE 
        QUEX_NAME(TokenQueue_destruct)(&me->_token_queue);
#       else
#           ifdef __QUEX_OPTION_PLAIN_C
            QUEX_NAME_TOKEN(destruct)(me->token);
#           endif
#       endif
    }

    QUEX_INLINE void 
    QUEX_NAME(Tokens_reset)(QUEX_TYPE_ANALYZER* me)
    {
#       ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
        QUEX_NAME(TokenQueue_reset)(&me->_token_queue);
#       else
        QUEX_NAME(Tokens_destruct(me));
        QUEX_NAME(Tokens_construct(me));
#       endif
    }

    QUEX_INLINE void
    QUEX_NAME(ModeStack_construct)(QUEX_TYPE_ANALYZER* me)
    {
        me->_mode_stack.end        = me->_mode_stack.begin;
        me->_mode_stack.memory_end = &me->_mode_stack.begin[QUEX_SETTING_MODE_STACK_SIZE];
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I */
