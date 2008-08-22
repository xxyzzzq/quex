/* -*- C++ -*- vim: set syntax=cpp: */

#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__

#include <quex/code_base/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/MemoryManager>

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex { 
#endif
    QUEX_INLINE void QuexBuffer_init(QuexBuffer*  me, const size_t Size, struct __QuexBufferFiller_tag* filler); 
    QUEX_INLINE void QuexBufferMemory_init(QuexBufferMemory* me, 
                                           QUEX_CHARACTER_TYPE* memory, size_t Size);

    TEMPLATE_IN(InputHandleT) void
    QuexBuffer_instantiate(QuexBuffer* me, InputHandleT* input_handle,
                           const char* IANA_InputCodingName, QuexBufferFillerTypeEnum FillerType,
                           const size_t BufferMemorySize,
                           const size_t TranslationBufferMemorySize)
    /* input_handle == 0x0 means that there is no stream/file to read from. Instead, the 
     *                     user intends to perform the lexical analysis directly on plain
     *                     memory. In this case, the user needs to call the following function
     *                     by hand in order to setup the memory:
     *
     *                     QuexBufferMemory_init(buffer->_memory, (uint8_t*)MyMemoryP, MyMemorySize); 
     */
    {
        QuexBufferFiller* buffer_filler = 0x0;

        if( input_handle != 0x0 ) {
            switch( FillerType ) {
            case QUEX_PLAIN: 
                QuexBufferFiller_Plain_init(buffer_filler, input_handle);
                break;
            case QUEX_ICONV: 
                buffer_filler = MemoryManager_get_BufferFiller(FillerType);
                QuexBufferFiller_IConv_init(buffer_filler, input_handle, 
                                            IANA_InputCodingName, 
                                            TranslationBufferMemorySize);
                break;
            }
            QuexBuffer_init(me, BufferMemorySize, buffer_filler);
        } else { 
            QuexBuffer_init(me, BufferMemorySize, 0x0);
        } 
    }

    TEMPLATE_IN(InputHandleT) void
    QuexBuffer_deinstantiate(QuexBuffer* me)
    {
        me->filler->_destroy(me->filler);
        MemoryManager_free_BufferMemory(me->_memory._front);
    }

    QUEX_INLINE void
    QuexBuffer_init(QuexBuffer*  me, const size_t Size, struct __QuexBufferFiller_tag* filler)
    {
        /* If filler == 0x0, then user wants to operate on plain memory, he has to call
         * QuexBufferMemory_init(...) by hand later.                                     */
        if( filler != 0x0 ) { 
            QuexBufferMemory_init(&(me->_memory), MemoryManager_get_BufferMemory(Size), Size);      
        } else { 
            QuexBufferMemory_init(&(me->_memory), 0, 0);      
        }

        me->_input_p        = me->_memory._front + 1;  /* First State does not increment */
        me->_lexeme_start_p = me->_memory._front + 1;  /* Thus, set it on your own.      */
        /* NOTE: The terminating zero is stored in the first character **after** the  
         *       lexeme (matching character sequence). The begin of line pre-condition  
         *       is concerned with the last character in the lexeme, which is the one  
         *       before the 'char_covered_by_terminating_zero'.*/
        me->_end_of_file_p                 = 0x0;
        me->_character_at_lexeme_start     = '\0';  /* (0 means: no character covered)*/
        me->_content_first_character_index = 0;
#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = '\n';  /* --> begin of line*/
#       endif
        me->filler = filler;

        if( filler != 0x0 ) {
#           ifdef QUEX_OPTION_ASSERTS
            __QUEX_STD_memset(me->_memory._front, 0, Size);
#           endif 
            /* If a real buffer filler is specified, then fill the memory. Otherwise, one 
             * assumes, that the user fills/has filled it with whatever his little heart desired. */
            const size_t LoadedN = me->filler->read_characters(me->filler, 
                                                               QuexBuffer_content_front(me), 
                                                               QuexBuffer_content_size(me));
            if( LoadedN != QuexBuffer_content_size(me) )  
                me->_end_of_file_p = QuexBuffer_content_front(me) + LoadedN;
        }
    }


    QUEX_INLINE void
    QuexBuffer_input_p_increment(QuexBuffer* buffer)
    { 
        ++(buffer->_input_p); 
    }

    QUEX_INLINE void
    QuexBuffer_input_p_decrement(QuexBuffer* buffer)
    { 
        --(buffer->_input_p); 
    }

    QUEX_INLINE void
    QuexBuffer_mark_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_lexeme_start_p = buffer->_input_p; 
    }

    QUEX_INLINE void
    QuexBuffer_seek_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_input_p = buffer->_lexeme_start_p;
    }

    QUEX_INLINE QUEX_CHARACTER_POSITION_TYPE
    QuexBuffer_tell_memory_adr(QuexBuffer* buffer)
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        QUEX_DEBUG_PRINT(buffer, "TELL: %i", (int)buffer->_input_p);
#       if      defined (QUEX_OPTION_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        return QUEX_CHARACTER_POSITION_TYPE(buffer->_input_p, buffer->_content_first_character_index);
#       else
        return (QUEX_CHARACTER_POSITION_TYPE)(buffer->_input_p);
#       endif
    }

    QUEX_INLINE void
    QuexBuffer_seek_memory_adr(QuexBuffer* buffer, QUEX_CHARACTER_POSITION_TYPE Position)
    {
#       if      defined (QUEX_OPTION_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        /* Check wether the memory_position is relative to the current start position   
         * of the stream. That means, that the tell_adr() command was called on the  
         * same buffer setting or the positions have been adapted using the += operator.*/
        __quex_assert(Position.buffer_start_position == buffer->_content_first_character_index);
        buffer->_input_p = Position.address;
#       else
        buffer->_input_p = Position;
#       endif
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    }

    QUEX_INLINE QUEX_CHARACTER_TYPE
    QuexBuffer_input_get(QuexBuffer* me)
    {
        QUEX_DEBUG_PRINT_INPUT(me, *(me->_input_p));
        return *(me->_input_p); 
    }

    QUEX_INLINE void
    QuexBuffer_store_last_character_of_lexeme_for_next_run(QuexBuffer* me)
    { 
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = *(me->_input_p - 1); 
#       endif
    }  

    QUEX_INLINE void
    QuexBuffer_set_terminating_zero_for_lexeme(QuexBuffer* me)
    { 
        me->_character_at_lexeme_start = *(me->_input_p); 
        *(me->_input_p) = '\0';
    }

    QUEX_INLINE void
    QuexBuffer_undo_terminating_zero_for_lexeme(QuexBuffer* me)
    {
        /* only need to reset, in case that the terminating zero was set*/
        if( me->_character_at_lexeme_start != (QUEX_CHARACTER_TYPE)'\0' ) {  
            *(me->_input_p) = me->_character_at_lexeme_start;                  
            me->_character_at_lexeme_start = (QUEX_CHARACTER_TYPE)'\0';     
        }
    }

    QUEX_INLINE QUEX_CHARACTER_TYPE*
    QuexBuffer_content_front(QuexBuffer* me)
    {
        return me->_memory._front + 1;
    }

    QUEX_INLINE QUEX_CHARACTER_TYPE*
    QuexBuffer_content_back(QuexBuffer* me)
    {
        return me->_memory._back - 1;
    }

    QUEX_INLINE size_t
    QuexBuffer_content_size(QuexBuffer* me)
    {
        return QuexBufferMemory_size(&(me->_memory)) - 2;
    }

    QUEX_INLINE void
    QuexBuffer_end_of_file_set(QuexBuffer* me, QUEX_CHARACTER_TYPE* Position)
    {
        __quex_assert(Position > me->_memory._front);
        __quex_assert(Position <= me->_memory._back);
        /* NOTE: The content starts at _front[1], since _front[0] contains 
         *       the buffer limit code. */
        me->_end_of_file_p    = Position;
        *(me->_end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    QUEX_INLINE void
    QuexBuffer_end_of_file_unset(QuexBuffer* buffer)
    {
        __quex_assert(buffer->_end_of_file_p <= buffer->_memory._back);
        buffer->_end_of_file_p = 0x0;
    }

    QUEX_INLINE bool 
    QuexBuffer_is_end_of_file(QuexBuffer* buffer)
    { 
        __quex_assert(buffer->_input_p != 0x0);
        return buffer->_input_p == buffer->_end_of_file_p;
    }

    QUEX_INLINE bool                  
    QuexBuffer_is_begin_of_file(QuexBuffer* buffer)
    { 
        if     ( buffer->_input_p != buffer->_memory._front )  return false;
        else if( buffer->_content_first_character_index != 0 ) return false;
        return true;
    }

    QUEX_INLINE void 
    QuexBufferMemory_init(QuexBufferMemory* me, 
                           QUEX_CHARACTER_TYPE* memory, size_t Size) 
    {
        /* The buffer memory can be initially be set to '0x0' if no buffer filler
         * is specified. Then the user has to call this function on his own in order
         * to specify the memory on which to rumble. */
        __quex_assert((Size != 0) || (memory == 0x0)); 

        if( Size == 0 ) { 
            me->_front = me->_back = 0;
            return;
        }
        /* Min(Size) = 2 characters for buffer limit code (front and back) + at least
         * one character to be read in forward direction. */
        __quex_assert(Size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2);
        me->_front    = memory;
        me->_back     = memory + (Size - 1);
        /* NOTE: We cannot set the memory all to zero at this point in time. It may be that the
         *       memory is already filled with content (e.g. by an external owner). The following
         *       code has deliberately be disabled:
         *           #ifdef QUEX_OPTION_ASSERTS
         *           __QUEX_STD_memset(me->_front, 0, Size);
         *           #endif 
         *       When the buffer uses a buffer filler, then it is a different ball game. Please,
         *       consider QuexBuffer_init().
         */
        *(me->_front) = QUEX_SETTING_BUFFER_LIMIT_CODE;
        *(me->_back)  = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }


    QUEX_INLINE size_t          
    QuexBufferMemory_size(QuexBufferMemory* me)
    { return me->_back - me->_front + 1; }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} /* namespace quex */
#endif

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__ */


