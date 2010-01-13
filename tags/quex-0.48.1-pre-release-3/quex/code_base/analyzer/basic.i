/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__BASIC_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__BASIC_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/analyzer/member/include-stack>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN
    struct QUEX_NAME(Mode_tag);

    TEMPLATE_IN(InputHandleT) void
    QUEX_FUNC(construct_basic)(QUEX_TYPE_ANALYZER*     me,
                               InputHandleT*           input_handle,
                               QUEX_TYPE_CHARACTER*    BufferMemory,
                               const size_t            BufferMemorySize,
                               const char*             CharacterEncodingName, 
                               const size_t            TranslationBufferMemorySize,
                               bool                    ByteOrderReversionF)
    /* input_handle == 0x0 means that there is no stream/file to read from. Instead, the 
     *                     user intends to perform the lexical analysis directly on plain
     *                     memory. In this case, the user needs to call the following function
     *                     by hand in order to setup the memory:
     *
     *                     QuexBufferMemory_construct(analyse->buffer._memory, 
     *                                                (uint8_t*)MyMemoryP, MyMemorySize); 
     */
    {
#       if      defined(QUEX_OPTION_ASSERTS) \
           && ! defined(QUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED)
        __QUEX_STD_printf(__QUEX_MESSAGE_ASSERTS_INFO);
#       endif
       
#       if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
        /* explict call of placement new for all tokens in the chunk */
        QUEX_NAME(TokenQueue_construct)(&me->_token_queue, QUEX_SETTING_TOKEN_QUEUE_SIZE);
#       elif defined(QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE)
        QUEX_NAME(TokenQueue_construct)(&me->_token_queue, 0);
#       else
        me->token = 0x0; /* call to 'receive(Token*)' provides pointer to some place in memory. */
#       endif
       
#       ifdef QUEX_OPTION_STRING_ACCUMULATOR
        QUEX_NAME(Accumulator_construct)(&me->accumulator, (QUEX_TYPE_ANALYZER*)me);
#       endif
       
#       ifdef __QUEX_OPTION_COUNTER
        QUEX_FIX(COUNTER, _construct)(&me->counter, me);
#       endif

#       ifdef QUEX_OPTION_ASSERTS
        /* Initialize everything to 0xFF which is most probably causing an error
         * if a member variable is not initialized before it is used.             */
        __QUEX_STD_memset((uint8_t*)&me->buffer, 0xFF, sizeof(me->buffer));
#       endif
        
#       ifdef  QUEX_OPTION_INCLUDE_STACK
        me->_parent_memento = 0x0;
#       endif

        me->_mode_stack.end        = me->_mode_stack.begin;
        me->_mode_stack.memory_end = me->_mode_stack.begin + QUEX_SETTING_MODE_STACK_SIZE;

        QUEX_NAME(Buffer_construct)(&me->buffer, input_handle, BufferMemory, BufferMemorySize,
                                    CharacterEncodingName, TranslationBufferMemorySize,
                                    ByteOrderReversionF);

        if( input_handle == 0x0 ) {
            /* TWO CASES:
             * (1) The user provides a buffer memory: --> assume it is filled to the end.
             * (2) The user does not provide memory:  --> the memory IS empty.             */
            if( BufferMemory == 0x0 ) {
                /* 'buffer._memory._front' has been set at this point in time.             */
                QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, me->buffer._memory._front + 1);
            }
            /* When working on plain memory, the '_end_of_file_p' must be set to indicate
             * the end of the content.                                                     */
            __quex_assert(me->buffer._memory._end_of_file_p != 0x0);
        }

        me->__file_handle_allocated_by_constructor = 0x0;
    }


    QUEX_INLINE void
    QUEX_FUNC(destruct_basic)(QUEX_TYPE_ANALYZER* me)
    {
        QUEX_NAME(Buffer_destruct)(&me->buffer);

#       ifdef QUEX_OPTION_STRING_ACCUMULATOR
        QUEX_NAME(Accumulator_destruct)(&me->accumulator);
#       endif
       
#       ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE 
        QUEX_NAME(TokenQueue_destruct)(&me->_token_queue);
#       endif
        if( me->__file_handle_allocated_by_constructor != 0x0 ) {
            __QUEX_STD_fclose(me->__file_handle_allocated_by_constructor); 
        }
    }

    TEMPLATE_IN(InputHandleT) void
    QUEX_FUNC(reset_basic)(QUEX_TYPE_ANALYZER*  me,
                           InputHandleT*        input_handle, 
                           const char*          CharacterEncodingName, 
                           const size_t         TranslationBufferMemorySize)
    {
#       ifdef __QUEX_OPTION_COUNTER
        QUEX_FIX(COUNTER, _reset)(&me->counter);
#       endif

#       ifdef __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASED
        QUEX_NAME(TokenQueue_reset)(&me->_token_queue);
#       endif

#       ifdef QUEX_OPTION_STRING_ACCUMULATOR
        me->accumulator.clear();
#       endif

#       ifdef QUEX_OPTION_INCLUDE_STACK
        QUEX_FUNC(include_stack_delete)((QUEX_TYPE_ANALYZER*)me);
#       endif

#       ifdef QUEX_OPTION_POST_CATEGORIZER
        me->post_categorizer.clear();
#       endif

        me->_mode_stack.end        = me->_mode_stack.begin;
        me->_mode_stack.memory_end = me->_mode_stack.begin + QUEX_SETTING_MODE_STACK_SIZE;

        QUEX_NAME(Buffer_reset)(&me->buffer, input_handle, CharacterEncodingName, TranslationBufferMemorySize);
    }

    /* NOTE: 'reload_forward()' needs to be implemented for each mode, because
     *       addresses related to acceptance positions need to be adapted. This
     *       is not the case for 'reload_backward()'. In no case of backward
     *       reloading, there are important addresses to keep track. */
    QUEX_INLINE bool 
    QUEX_FUNC(buffer_reload_backward)(QUEX_NAME(Buffer)* buffer)
    {
        if( buffer->filler == 0x0 ) return false;

        const size_t LoadedCharacterN = QUEX_NAME(BufferFiller_load_backward)(buffer);
        if( LoadedCharacterN == 0 ) return false;
        
        /* Backward lexing happens in two cases:
         *
         *  (1) When checking for a pre-condition. In this case, no dedicated acceptance
         *      is involved. No acceptance positions are considered.
         *  (2) When tracing back to get the end of a core pattern in pseudo-ambigous
         *      post conditions. Then, no acceptance positions are involved, because
         *      the start of the lexeme shall not drop before the begin of the buffer 
         *      and the end of the core pattern, is of course, after the start of the 
         *      lexeme. => there will be no reload backwards.                            */
        return true;
    }

    QUEX_INLINE bool 
    QUEX_FUNC(buffer_reload_forward)(QUEX_NAME(Buffer)* buffer, 
                                     QUEX_TYPE_CHARACTER_POSITION* last_acceptance_input_position,
                                     QUEX_TYPE_CHARACTER_POSITION* post_context_start_position,
                                     const size_t                  PostContextN)
    {
        QUEX_TYPE_CHARACTER_POSITION* iterator = 0x0;
        QUEX_TYPE_CHARACTER_POSITION* End = post_context_start_position + PostContextN;

        if( buffer->filler == 0x0 ) return false;
        if( buffer->_memory._end_of_file_p != 0x0 ) return false;
        const size_t LoadedCharacterN = QUEX_NAME(BufferFiller_load_forward)(buffer);
        if( LoadedCharacterN == 0 ) return false;

        if( *last_acceptance_input_position != 0x0 ) { 
            *last_acceptance_input_position -= LoadedCharacterN;
        }                                                                  
        for(iterator = post_context_start_position; iterator != End; ++iterator) {
            /* NOTE: When the post_context_start_position is still undefined the following operation may
             *       underflow. But, do not care, once it is **assigned** to a meaningful value, it won't */
            *iterator -= LoadedCharacterN;
        }
                                                                              
        return true;
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>


#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__BASIC_I */
