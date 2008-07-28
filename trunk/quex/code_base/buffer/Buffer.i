/* -*- C++ -*- vim: set syntax=cpp: */

#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__

#include <quex/code_base/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer_debug.i>

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex { 
#endif

    QUEX_INLINE_KEYWORD void 
    QuexBufferMemory_setup(QuexBufferMemory* me, 
                           QUEX_CHARACTER_TYPE* memory, size_t Size, 
                           bool ExternalOwnerF) 
    {
        me->_front    = memory;
        me->_back     = memory + (Size - 1);
#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset(me->_front, 0, Size);
#       endif
        *(me->_front) = QUEX_SETTING_BUFFER_LIMIT_CODE;
        *(me->_back)  = QUEX_SETTING_BUFFER_LIMIT_CODE;
        me->_external_owner_f = ExternalOwnerF;
    }


    QUEX_INLINE_KEYWORD size_t          
    QuexBufferMemory_size(QuexBufferMemory* me)
    { return me->_back - me->_front + 1; }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_init(QuexBuffer*          me, 
                    QUEX_CHARACTER_TYPE* memory_chunk, const size_t Size)
    {
        if( memory_chunk != 0x0 ) 
            QuexBufferMemory_setup(&(me->_memory), memory_chunk, Size, /* ExternalOwnerF */ true);      
        else 
            QuexBufferMemory_setup(&(me->_memory), __QUEX_ALLOCATE_MEMORY(QUEX_CHARACTER_TYPE, Size), Size, false);      

        me->_input_p        = me->_memory._front + 1;  /* First State does not increment */
        me->_lexeme_start_p = me->_memory._front + 1;
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
    }


    QUEX_INLINE_KEYWORD void
    QuexBuffer_input_p_increment(QuexBuffer* buffer)
    { 
        ++(buffer->_input_p); 
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_input_p_decrement(QuexBuffer* buffer)
    { 
        --(buffer->_input_p); 
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_mark_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_lexeme_start_p = buffer->_input_p; 
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_seek_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_input_p = buffer->_lexeme_start_p;
    }

    QUEX_INLINE_KEYWORD QUEX_CHARACTER_POSITION_TYPE
    QuexBuffer_tell_memory_adr(QuexBuffer* buffer)
    {
        /* QUEX_BUFFER_ASSERT_CONSISTENCY();*/
        QUEX_DEBUG_PRINT(buffer, "TELL: %i", (int)buffer->_input_p);
#       if      defined (QUEX_OPTION_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        return QUEX_CHARACTER_POSITION_TYPE(buffer->_input_p, buffer->_content_first_character_index);
#       else
        return (QUEX_CHARACTER_POSITION_TYPE)(buffer->_input_p);
#       endif
    }

    QUEX_INLINE_KEYWORD void
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
        /* QUEX_BUFFER_ASSERT_CONSISTENCY(); */
    }

    QUEX_INLINE_KEYWORD QUEX_CHARACTER_TYPE
    QuexBuffer_input_get(QuexBuffer* me)
    {
        QUEX_DEBUG_PRINT_INPUT(me, *(me->_input_p));
        return *(me->_input_p); 
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_store_last_character_of_lexeme_for_next_run(QuexBuffer* me)
    { 
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = *(me->_input_p - 1); 
#       endif
    }  

    QUEX_INLINE_KEYWORD void
    QuexBuffer_set_terminating_zero_for_lexeme(QuexBuffer* me)
    { 
        me->_character_at_lexeme_start = *(me->_input_p); 
        *(me->_input_p) = '\0';
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_undo_terminating_zero_for_lexeme(QuexBuffer* me)
    {
        /* only need to reset, in case that the terminating zero was set*/
        if( me->_character_at_lexeme_start != (QUEX_CHARACTER_TYPE)'\0' ) {  
            *(me->_input_p) = me->_character_at_lexeme_start;                  
            me->_character_at_lexeme_start = (QUEX_CHARACTER_TYPE)'\0';     
        }
    }

    QUEX_INLINE_KEYWORD QUEX_CHARACTER_TYPE*
    QuexBuffer_content_front(QuexBuffer* me)
    {
        return me->_memory._front + 1;
    }

    QUEX_INLINE_KEYWORD QUEX_CHARACTER_TYPE*
    QuexBuffer_content_back(QuexBuffer* me)
    {
        return me->_memory._back - 1;
    }

    QUEX_INLINE_KEYWORD size_t
    QuexBuffer_content_size(QuexBuffer* me)
    {
        return QuexBufferMemory_size(&(me->_memory)) - 2;
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_end_of_file_set(QuexBuffer* me, QUEX_CHARACTER_TYPE* Position)
    {
        __quex_assert(Position > me->_memory._front);
        __quex_assert(Position <= me->_memory._back);
        /* NOTE: The content starts at _front[1], since _front[0] contains 
         *       the buffer limit code. */
        me->_end_of_file_p    = Position;
        *(me->_end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    QUEX_INLINE_KEYWORD void
    QuexBuffer_end_of_file_unset(QuexBuffer* buffer)
    {
        __quex_assert(buffer->_end_of_file_p <= buffer->_memory._back);
        buffer->_end_of_file_p = 0x0;
    }

    QUEX_INLINE_KEYWORD bool 
    QuexBuffer_is_end_of_file(QuexBuffer* buffer)
    { 
        __quex_assert(buffer->_input_p != 0x0);
        return buffer->_input_p == buffer->_end_of_file_p;
    }

    QUEX_INLINE_KEYWORD bool                  
    QuexBuffer_is_begin_of_file(QuexBuffer* buffer)
    { 
        if     ( buffer->_input_p != buffer->_memory._front )  return false;
        else if( buffer->_content_first_character_index != 0 ) return false;
        return true;
    }

#if ! defined(__QUEX_SETTING_PLAIN_C)
} /* namespace quex */
#endif

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__ */


