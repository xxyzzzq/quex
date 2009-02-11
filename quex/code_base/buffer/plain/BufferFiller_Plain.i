/*  -*- C++ -*-  vim: set syntax=cpp: */
/* (C) 2008 Frank-Rene Schaefer*/
#ifndef __INCLUDE_GUARD__QUEX_BUFFER__BUFFER_FILLER_PLAIN_I__
#define __INCLUDE_GUARD__QUEX_BUFFER__BUFFER_FILLER_PLAIN_I__
/**/

#if ! defined (__QUEX_SETTING_PLAIN_C)
#   include <iostream> 
#   include <cerrno>
#   include <stdexcept>
#endif
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/InputPolicy>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/MemoryManager>

#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif

#   ifndef __QUEX_SETTING_PLAIN_C
#   define TEMPLATED(CLASS)   CLASS<InputHandleT>
#   else
#   define TEMPLATED(CLASS)   CLASS
#   endif

    TEMPLATE_IN(InputHandleT) size_t __BufferFiller_Plain_tell_character_index(QuexBufferFiller* alter_ego);
    TEMPLATE_IN(InputHandleT) void   __BufferFiller_Plain_seek_character_index(QuexBufferFiller* alter_ego, 
                                                                               const size_t      CharacterIndex); 
    TEMPLATE_IN(InputHandleT) size_t __BufferFiller_Plain_read_characters(QuexBufferFiller*    alter_ego,
                                                                          QUEX_CHARACTER_TYPE* start_of_buffer, 
                                                                          const size_t         N);
    TEMPLATE_IN(InputHandleT) void   __BufferFiller_Plain_destroy(QuexBufferFiller* alter_ego);

    TEMPLATE_IN(InputHandleT) TEMPLATED(QuexBufferFiller_Plain)*
    QuexBufferFiller_Plain_new(InputHandleT*    input_handle)
    {
        TEMPLATED(QuexBufferFiller_Plain)*  me = TEMPLATED(MemoryManager_BufferFiller_Plain_allocate)();
        __quex_assert(me != 0x0);
        __quex_assert(input_handle != 0x0);

        __QuexBufferFiller_init_functions(&me->base,
                                          TEMPLATED(__BufferFiller_Plain_tell_character_index),
                                          TEMPLATED(__BufferFiller_Plain_seek_character_index), 
                                          TEMPLATED(__BufferFiller_Plain_read_characters),
                                          TEMPLATED(__BufferFiller_Plain_destroy));
        /**/
        me->ih             = input_handle;
        me->start_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        me->_character_index = 0;
#       endif
        me->_last_stream_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);

        return me;
    }

    TEMPLATE_IN(InputHandleT) void 
    __BufferFiller_Plain_destroy(QuexBufferFiller* alter_ego) 
    {
        TEMPLATED(QuexBufferFiller_Plain)* me = (TEMPLATED(QuexBufferFiller_Plain)*)alter_ego;
        MemoryManager_BufferFiller_Plain_free(me);

    }

    TEMPLATE_IN(InputHandleT) size_t 
    __BufferFiller_Plain_tell_character_index(QuexBufferFiller* alter_ego) 
    { 
       __quex_assert(alter_ego != 0x0); 
       /* The type cast is necessary, since the function signature needs to 
        * work with the first argument being of base class type. */
       TEMPLATED(QuexBufferFiller_Plain)* me = (TEMPLATED(QuexBufferFiller_Plain)*)alter_ego;

       __quex_assert(me->ih != 0x0); 
       /* Ensure, that the stream position is only influenced by
        *    __read_characters(...) 
        *    __seek_character_index(...)                                                          */
       __quex_assert(me->_last_stream_position == QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT)); 
#      ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
       return me->_character_index;
#      endif
       return (size_t)(me->_last_stream_position - me->start_position) / sizeof(QUEX_CHARACTER_TYPE);
    }

#   if ! defined(QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION)
    /* NOTE: This differs from QuexBuffer_seek(...) in the sense, that it only sets the
     *       stream to a particular position given by a character index. QuexBuffer_seek(..)
     *       sets the _input_p to a particular position.                                      */
    TEMPLATE_IN(InputHandleT) void 
    __BufferFiller_Plain_seek_character_index(QuexBufferFiller* alter_ego, const size_t CharacterIndex) 
    { 
        __quex_assert(alter_ego != 0x0); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type. */
        TEMPLATED(QuexBufferFiller_Plain)* me = (TEMPLATED(QuexBufferFiller_Plain)*)alter_ego;
        __quex_assert(me->ih != 0x0); 

        long avoid_tmp_arg = (long)(CharacterIndex * sizeof(QUEX_CHARACTER_TYPE) + me->start_position); 
        QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, avoid_tmp_arg);
        me->_last_stream_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
    }
#   else
    /* Implementation for 'strange streams', i.e. streams where the input position increase is not
     * necessarily proportional to the amount of read-in characters. Note, that the seek function is
     * the only function that is significantly different for this case.                           */
    TEMPLATE_IN(InputHandleT) void 
    __BufferFiller_Plain_seek_character_index(QuexBufferFiller* alter_ego, const size_t CharacterIndex) 
    { 
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED(QuexBufferFiller_Plain)* me = (TEMPLATED(QuexBufferFiller_Plain)*)alter_ego;
        __quex_assert(me->ih != 0x0); 

        if     ( me->_character_index == CharacterIndex ) return;
        else if( me->_character_index < CharacterIndex ) {
            __QuexBufferFiller_step_forward_n_characters(alter_ego, CharacterIndex - me->_character_index);
        }
        else { /* me->_character_index > CharacterIndex */
            QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, me->start_position);
            __QuexBufferFiller_step_forward_n_characters(alter_ego, CharacterIndex);
        }
        me->_last_stream_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
    }
#   endif

    TEMPLATE_IN(InputHandleT) size_t   
    __BufferFiller_Plain_read_characters(QuexBufferFiller*    alter_ego,
                                         QUEX_CHARACTER_TYPE* buffer_memory, const size_t N)  
    { 
        __quex_assert(alter_ego != 0x0); 
        __quex_assert(buffer_memory != 0x0); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type. */
        TEMPLATED(QuexBufferFiller_Plain)* me = (TEMPLATED(QuexBufferFiller_Plain)*)alter_ego;
#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset((uint8_t*)buffer_memory, 0xFF, N * sizeof(QUEX_CHARACTER_TYPE));
#       endif

        __quex_assert(me->ih != 0x0); 
        const size_t ByteN = QUEX_INPUT_POLICY_LOAD_BYTES(me->ih, InputHandleT, 
                                                          buffer_memory, N * sizeof(QUEX_CHARACTER_TYPE));

        if( ByteN % sizeof(QUEX_CHARACTER_TYPE) != 0 ) 
            QUEX_ERROR_EXIT("Error: End of file cuts in the middle a multi-byte character.");
        const size_t   CharacterN = ByteN / sizeof(QUEX_CHARACTER_TYPE); 

#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        me->_character_index += CharacterN;
#       endif
        me->_last_stream_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
        return CharacterN;
    }

#   undef TEMPLATED_CLASS

#if ! defined (__QUEX_SETTING_PLAIN_C)
}  /* namespace quex*/
#endif

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>
#endif /* __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_PLAIN_I__ */
