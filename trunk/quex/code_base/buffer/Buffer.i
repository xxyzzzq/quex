// -*- C++ -*- vim: set syntax=cpp:

#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__

#include <quex/code_base/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer_debug.i>

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex { 
#endif

#if ! defined(__QUEX_SETTING_PLAIN_C)
#    define TEMPLATE_IN    template <class CharacterCarrierType> inline

#    define BUFFER_TYPE               quex::Buffer<CharacterCarrierType>
#    define BUFFER_MEMORY_TYPE        quex::BufferMemory<CharacterCarrierType>
#    define BUFFER_FILLER_TYPE        quex::QuexBufferFiller<CharacterCarrierType>
#    define MINIMAL_ANALYZER_TYPE     quex::QuexAnalyserMinimal<CharacterCarrierType>
    
#    define __BUFFER_GET_BUFFER_LIMIT_CODE(buffer)  ()
#    define __BUFFER_IS_BEGIN_OF_FILE(buffer)       (buffer->is_begin_of_file())
#    define __ALLOCATE_MEMORY(N)                    (new CharacterCarrierType[(size_t)N]);

#else
#    define CharacterCarrierType QUEX_CHARACTER_TYPE  
#    define TEMPLATE_IN             /* no template */ static
#    define BUFFER_TYPE             QuexBufferCore
#    define BUFFER_MEMORY_TYPE      BufferMemory
#    define BUFFER_FILLER_TYPE      QuexBufferFiller
#    define MINIMAL_ANALYZER_TYPE   QuexAnalyserMinimal

#    define __BUFFER_GET_BUFFER_LIMIT_CODE(buffer)  (QUEX_SETTING_BUFFER_LIMIT_CODE)
#    define __BUFFER_IS_BEGIN_OF_FILE(buffer)       (buffer->_input_p == me->_buffer_begin - 1)
#    define __ALLOCATE_MEMORY(N)                    (CharacterCarrierType*)malloc(sizeof(CharacterCarrierType)*(size_t)N)

#endif
       

    TEMPLATE_IN void 
    BufferMemory_setup(BUFFER_MEMORY_TYPE* bmem, CharacterCarrierType* memory, size_t Size, 
                       bool ExternalOwnerF, CharacterCarrierType BLC) 
    {
        bmem->_front    = memory;
        bmem->_back     = memory + (Size - 1);
#       ifdef QUEX_OPTION_ACTIVATE_ASSERTS
        memset(bmem->front, 0, Size);
#       endif
        *(bmem->_front) = BLC; // buffer limit code
        *(bmem->_back)  = BLC; // buffer limit code
        bmem->_external_owner_f = ExternalOwnerF;
    }


    TEMPLATE_IN size_t          
    BufferMemory_size(BUFFER_MEMORY_TYPE* bmem)
    { return bmem->_back - bmem->_front + 1; }

    TEMPLATE_IN void
    QuexBufferCore_init(BUFFER_TYPE*          me, 
                        CharacterCarrierType* memory_chunk, size_t Size, 
                        CharacterCarrierType  BLC)
    {
        if( memory_chunk != 0x0 ) 
            BufferMemory_setup(&(me->_memory), memory_chunk, Size, /* ExternalOwnerF */ true, BLC);      
        else 
            BufferMemory_setup(&(me->_memory), __ALLOCATE_MEMORY(Size), Size, false, BLC);      

        me->_input_p        = me->_memory._front + 1;  /* First State does not increment */
        me->_lexeme_start_p = me->_memory._front + 1;
        // NOTE: The terminating zero is stored in the first character **after** the
        //       lexeme (matching character sequence). The begin of line pre-condition
        //       is concerned with the last character in the lexeme, which is the one
        //       before the 'char_covered_by_terminating_zero'.
        me->_end_of_file_p    = 0x0;
        me->_character_at_lexeme_start     = '\0';  // (0 means: no character covered)
#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = '\n';  // --> begin of line
#       endif
    }

    TEMPLATE_IN void
    QuexAnalyserMinimal_init(MINIMAL_ANALYZER_TYPE* me,
                             __QUEX_SETTING_ANALYSER_FUNCTION_RETURN_TYPE (*AnalyserFunction)(QuexAnalyserMinimal*),
                             CharacterCarrierType* memory_chunk, size_t Size, 
                             CharacterCarrierType  BLC,
                             QuexBufferFiller*     BufferFiller)
    {
        QuexBufferCore_init(&me->buffer, memory_chunk, Size, BLC);
        me->current_analyser_function = AnalyserFunction;
        me->buffer_filler             = BufferFiller;
        if( BufferFiller != 0x0 ) me->buffer_filler->client = &me->buffer;
    }

    TEMPLATE_IN void
    Buffer_input_p_increment(BUFFER_TYPE* buffer)
    { 
        ++(buffer->_input_p); 
    }

    TEMPLATE_IN void
    Buffer_input_p_decrement(BUFFER_TYPE* buffer)
    { 
        --(buffer->_input_p); 
    }

    TEMPLATE_IN void
    Buffer_mark_lexeme_start(BUFFER_TYPE* buffer)
    { 
        buffer->_lexeme_start_p = buffer->_input_p; 
    }

    TEMPLATE_IN void
    Buffer_seek_lexeme_start(BUFFER_TYPE* buffer)
    { 
        buffer->_input_p = buffer->_lexeme_start_p;
    }

    TEMPLATE_IN QUEX_CHARACTER_POSITION_TYPE
    Buffer_tell_adr(BUFFER_TYPE* buffer)
    {
        // QUEX_BUFFER_ASSERT_CONSISTENCY();
        QUEX_DEBUG_PRINT(buffer, "TELL: %i", (int)buffer->_input_p);
#       if      defined (QUEX_OPTION_ACTIVATE_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        return QUEX_CHARACTER_POSITION_TYPE(buffer->_input_p, buffer->_character_index_at_front);
#       else
        return (QUEX_CHARACTER_POSITION_TYPE)(buffer->_input_p);
#       endif
    }

    TEMPLATE_IN void
    Buffer_seek_adr(BUFFER_TYPE* buffer, QUEX_CHARACTER_POSITION_TYPE Position)
    {
#       if      defined (QUEX_OPTION_ACTIVATE_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        // Check wether the memory_position is relative to the current start position 
        // of the stream. That means, that the tell_adr() command was called on the
        // same buffer setting or the positions have been adapted using the += operator.
        __quex_assert(Position.buffer_start_position == buffer->_character_index_at_front);
        buffer->_input_p = Position.address;
#       else
        buffer->_input_p = Position;
#       endif
        // QUEX_BUFFER_ASSERT_CONSISTENCY();
    }

    TEMPLATE_IN CharacterCarrierType
    Buffer_input_get(BUFFER_TYPE* me)
    {
        QUEX_DEBUG_PRINT_INPUT(me, *(me->_input_p));
        return *(me->_input_p); 
    }

    TEMPLATE_IN void
    Buffer_store_last_character_of_lexeme_for_next_run(BUFFER_TYPE* me)
    { 
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = *(me->_input_p - 1); 
#       endif
    }  

    TEMPLATE_IN void
    Buffer_set_terminating_zero_for_lexeme(BUFFER_TYPE* me)
    { 
        me->_character_at_lexeme_start = *(me->_input_p); 
        *(me->_input_p) = '\0';
    }

    TEMPLATE_IN void
    Buffer_undo_terminating_zero_for_lexeme(BUFFER_TYPE* me)
    {
        // only need to reset, in case that the terminating zero was set
        if( me->_character_at_lexeme_start != (CharacterCarrierType)'\0' ) {  
            *(me->_input_p) = me->_character_at_lexeme_start;                  
            me->_character_at_lexeme_start = (CharacterCarrierType)'\0';     
        }
    }

    TEMPLATE_IN CharacterCarrierType*
    Buffer_content_front(BUFFER_TYPE* me)
    {
        return me->_memory._front + 1;
    }

    TEMPLATE_IN CharacterCarrierType*
    Buffer_content_back(BUFFER_TYPE* me)
    {
        return me->_memory._back - 1;
    }

    TEMPLATE_IN size_t
    Buffer_content_size(BUFFER_TYPE* me)
    {
        return BufferMemory_size(&(me->_memory)) - 2;
    }

    TEMPLATE_IN void
    Buffer_end_of_file_set(BUFFER_TYPE* me, CharacterCarrierType* Position)
    {
        __quex_assert(Position > me->_memory._front);
        __quex_assert(Position <= me->_memory._back);
        // NOTE: The content starts at _front[1], since _front[0] contains 
        //       the buffer limit code.
        me->_end_of_file_p = Position;
        *(me->_end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    TEMPLATE_IN void
    Buffer_end_of_file_unset(BUFFER_TYPE* buffer)
    {
        __quex_assert(buffer->_end_of_file_p <= _memory._back);
        buffer->_end_of_file_p = 0x0;
    }

    TEMPLATE_IN bool 
    Buffer_is_end_of_file(BUFFER_TYPE* buffer)
    { 
        __quex_assert(buffer->_input != 0x0);
        return buffer->_input_p == buffer->_end_of_file_p;
    }

    TEMPLATE_IN bool                  
    Buffer_is_begin_of_file(BUFFER_TYPE* buffer)
    { 
        if     ( buffer->_input_p != buffer->_memory._front )  return false;
        else if( buffer->_content_first_character_index != 0 ) return false;
        return true;
    }

    TEMPLATE_IN CharacterCarrierType  
    Buffer_get_BLC(BUFFER_TYPE* me)
    { 
        /* The buffer limit code can be made buffer specific. However, this has
         * a significant influence on analysis speed */
        return QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

#   undef TEMPLATE_IN
#   undef BUFFER_TYPE
#   undef BUFFER_MEMORY_TYPE
#   undef BUFFER_FILLER_TYPE
#   undef MINIMAL_ANALYZER_TYPE
    
#   undef __BUFFER_LOAD_FORWARD
#   undef __BUFFER_LOAD_BACKWARD
#   undef __ALLOCATE_MEMORY

#if ! defined(__QUEX_SETTING_PLAIN_C)
} // namespace quex
#endif



#endif // __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__


