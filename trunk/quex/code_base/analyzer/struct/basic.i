/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I

#include    <quex/code_base/definitions>
#include    <quex/code_base/buffer/Buffer>
#include    <quex/code_base/buffer/BufferFiller>
#include    <quex/code_base/buffer/asserts>
#ifdef      QUEX_OPTION_INCLUDE_STACK
#   include <quex/code_base/analyzer/member/include-stack>
#endif

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN
    struct QUEX_NAME(Mode_tag);

    QUEX_INLINE void QUEX_NAME(Asserts_construct)(const char* CharacterEncodingName);
    QUEX_INLINE void QUEX_NAME(Tokens_construct)(QUEX_TYPE_ANALYZER* me);
    QUEX_INLINE void QUEX_NAME(Tokens_reset)(QUEX_TYPE_ANALYZER* me);
    QUEX_INLINE void QUEX_NAME(Tokens_destruct)(QUEX_TYPE_ANALYZER* me);
    QUEX_INLINE void QUEX_NAME(ModeStack_construct)(QUEX_TYPE_ANALYZER* me);
    QUEX_INLINE void QUEX_NAME(BufferFiller_DEFAULT)(QUEX_TYPE_ANALYZER* me);

    QUEX_INLINE void
    QUEX_NAME(construct_from_byte_loader)(QUEX_TYPE_ANALYZER*  me,
                                          ByteLoader*          byte_loader,
                                          const char*          CharacterEncodingName) 
    {
        QUEX_NAME(BufferFiller)* filler;
        QUEX_NAME(Asserts_construct)(CharacterEncodingName);

        filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, 
                                                 CharacterCodecName);
        
        QUEX_NAME(construct_from_buffer_filler)(me, filler);
    }

    QUEX_INLINE void
    QUEX_NAME(construct_from_buffer_filler)(QUEX_TYPE_ANALYZER*  me,
                                            QUEX_NAME(BufferFiller)* filler)
    {
        QUEX_NAME(Buffer_construct)(&me->buffer, filler,
                                    QUEX_SETTING_BUFFER_SIZE); 
        QUEX_NAME(construct_basic)(me)
    }

    QUEX_INLINE void
    QUEX_NAME(construct_from_memory)(QUEX_TYPE_ANALYZER*     me,
                                     QUEX_TYPE_CHARACTER*    Memory,
                                     const size_t            MemorySize,
                                     QUEX_TYPE_CHARACTER*    EndOfFileP)
    /* When memory is provided from extern, the 'external entity' is
     * responsible for filling it. There is no 'file/stream handle', no 'byte
     * loader', and 'no buffer filler'.                                      */
    {
        QUEX_NAME(Buffer_construct_with_memory)(&me->buffer, 
                                                QUEX_NAME(BufferFiller*)0,
                                                Memory, MemorySize, EndOfFileP,
                                                /* External */ true);
        QUEX_NAME(construct_basic)(me)
    }

    QUEX_INLINE void
    QUEX_NAME(construct_basic)(QUEX_TYPE_ANALYZER* me)
    {
        me->memory_allocate = QUEXED(MemoryManager_allocate);
        me->memory_free     = QUEXED(MemoryManager_free);

        QUEX_NAME(Tokens_construct)(me);
        QUEX_NAME(ModeStack_construct)(me);
        __QUEX_IF_INCLUDE_STACK(     me->_parent_memento = (QUEX_NAME(Memento)*)0);
        __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_construct)(&me->accumulator, me));
        __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_construct)(&me->post_categorizer));
        __QUEX_IF_COUNT(             QUEX_NAME(Counter_construct)(&me->counter); )

        QUEX_NAME(set_mode_brutally)(me, me->mode_db[__QUEX_SETTING_INITIAL_LEXER_MODE_ID]);
    }

    QUEX_INLINE void
    QUEX_NAME(reset_with_byte_loader)(QUEX_TYPE_ANALYZER*     me,
                                      const QUEX_NAME(Mode)*  Mode, 
                                      ByteLoader*             byte_loader) 
        /* Reset of Components of the Lexical Analyzer Engine ____________________________*/
    {
        QUEX_NAME(BufferFiller)* filler;

        if( me->buffer.filler ) {
            me->buffer.filler->delete_self(me->buffer.filler);
        }

        filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, 
                                                 CharacterCodecName);


        QUEX_NAME(reset_with_buffer_filler)(me, Mode, filler);
    }

    QUEX_INLINE void
    QUEX_NAME(reset_with_buffer_filler)(QUEX_TYPE_ANALYZER*      me,
                                        const QUEX_NAME(Mode)*   Mode, 
                                        QUEX_NAME(BufferFiller)* filler)
    { 
        QUEX_NAME(Buffer_init_analyzis)(&me->buffer, filler, 
                                        me->buffer._byte_order_reversion_active_f);

        QUEX_NAME(Tokens_reset)(me);

        QUEX_NAME(ModeStack_construct)(me);
        __QUEX_IF_INCLUDE_STACK(QUEX_NAME(include_stack_delete)((QUEX_TYPE_ANALYZER*)me));
        /* IMPORTANT: THE ACCUMULATOR CAN ONLY BE DESTRUCTED AFTER THE INCLUDE *
         *            STACK HAS BEEN DELETED. OTHERWISE, THERE MIGHT BE LEAKS. */
        __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_clear)(&me->accumulator));
        __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_destruct)(&me->post_categorizer));
        __QUEX_IF_POST_CATEGORIZER(  QUEX_NAME(PostCategorizer_construct)(&me->post_categorizer));
        __QUEX_IF_COUNT(             QUEX_NAME(Counter_construct)(&me->counter); )

        QUEX_NAME(set_mode_brutally)(me, (QUEX_NAME(Mode)*)Mode);
    }

    QUEX_INLINE void
    QUEX_NAME(destruct_basic)(QUEX_TYPE_ANALYZER* me)
    {
        QUEX_NAME(Tokens_destruct)(me);
        __QUEX_IF_INCLUDE_STACK(QUEX_NAME(include_stack_delete)((QUEX_TYPE_ANALYZER*)me));
        /* IMPORTANT: THE ACCUMULATOR CAN ONLY BE DESTRUCTED AFTER THE INCLUDE 
         *            STACK HAS BEEN DELETED. OTHERWISE, THERE MIGHT BE LEAKS. 
         * TODO: Why? I cannot see a reason <fschaef 15y08m03d>                */
        __QUEX_IF_STRING_ACCUMULATOR(QUEX_NAME(Accumulator_destruct)(&me->accumulator));
        __QUEX_IF_POST_CATEGORIZER(QUEX_NAME(PostCategorizer_destruct)(&me->post_categorizer));

        QUEX_NAME(Buffer_destruct)(&me->buffer);
    }


#   ifdef QUEX_OPTION_INCLUDE_STACK
    QUEX_INLINE void
    QUEX_NAME(include_push_byte_loader)(QUEX_TYPE_ANALYZER*     me,
                                        const QUEX_NAME(Mode)*  Mode, 
                                        ByteLoader*             byte_loader,
                                        const char*             CharacterCodecName /* = 0x0 */)
    {
        QUEX_NAME(BufferFiller*) filler;
       
        filler = QUEX_NAME(BufferFiller_DEFAULT)(byte_loader, 
                                                 CharacterCodecName);

        QUEX_NAME(include_push_buffer_filler)(me, Mode, filler);
    }

    QUEX_INLINE void
    QUEX_NAME(include_push_buffer_filler)(QUEX_TYPE_ANALYZER*      me,
                                          const QUEX_NAME(Mode)*   Mode, 
                                          QUEX_NAME(BufferFiller)* filler)
    {
        QUEX_NAME(Memento)*      m = QUEX_NAME(memento_pack)(me, byte_loader);

        QUEX_NAME(Buffer_construct)(&me->buffer, filler,
                                    0x0, QUEX_SETTING_BUFFER_SIZE, 0x0,
                                    me->buffer._byte_order_reversion_active_f);

        __QUEX_IF_INCLUDE_STACK(me->_parent_memento = m);
        __QUEX_IF_COUNT( QUEX_NAME(Counter_construct)(&me->counter); )

        QUEX_NAME(set_mode_brutally)(me, (QUEX_NAME(Mode)*)Mode);
    }   

    QUEX_INLINE bool
    QUEX_NAME(include_pop)(QUEX_TYPE_ANALYZER* me) 
    {
        /* Not included? return 'false' to indicate we're on the top level   */
        if( ! me->_parent_memento ) return false; 

        QUEX_NAME(Buffer_destruct)(&me->buffer);
        /* memento_unpack():
         *    => Current mode
         *           => __current_mode_p 
         *              current_analyzer_function                                       
         *              DEBUG_analyzer_function_at_entry                                   
         *    => Line/Column Counters
         *
         * Unchanged by memento_unpack():
         *    -- Mode stac
         *    -- Tokens and token queues.
         *    -- Accumulator.
         *    -- Post categorizer.
         *    -- File handle by constructor                                  */
              
        /* Copy Back of content that was stored upon inclusion.              */
        QUEX_NAME(memento_unpack)(me, me->_parent_memento);

        /* Return to including file succesful */
        return true;
    }

#   endif /* QUEX_OPTION_INCLUDE_STACK */


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

    QUEX_INLINE QUEX_NAME(BufferFiller)* 
    QUEX_NAME(BufferFiller_DEFAULT)(ByteLoader*   byte_loader, 
                                    const char*   CharacterEncodingName) 
    {
#       ifdef QUEX_OPTION_CONVERTER_ICU
        QUEX_NAME(Converter)* (*converters_new)(void) = QUEX_NAME(Converter_ICU_new);
#       elif defined(QUEX_OPTION_CONVERTER_ICONV)
        QUEX_NAME(Converter)* (*converters_new)(void) = QUEX_NAME(Converter_IConv_new);
#       else
        QUEX_NAME(Converter)* (*converters_new)(void) = 0;
#       endif

        return QUEX_NAME(BufferFiller_new)(byte_loader, converters_new,
                                           CharacterEncodingName, 
                                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BASIC_I */
