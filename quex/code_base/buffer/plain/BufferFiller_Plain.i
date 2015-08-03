/*  -*- C++ -*-  vim: set syntax=cpp: */
/* (C) 2008 Frank-Rene Schaefer*/
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__PLAIN__BUFFER_FILLER_PLAIN_I
#define __QUEX_INCLUDE_GUARD__BUFFER__PLAIN__BUFFER_FILLER_PLAIN_I
/**/

#if ! defined (__QUEX_OPTION_PLAIN_C)
#   include <iostream> 
#   include <cerrno>
#   include <stdexcept>
#endif
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/MemoryManager>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_Plain_construct)(QUEX_NAME(BufferFiller_Plain)*, ByteLoader* byte_loader);

    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

    QUEX_INLINE ptrdiff_t 
    QUEX_NAME(BufferFiller_Plain_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego);

    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Plain_seek_character_index)(QUEX_NAME(BufferFiller)*  alter_ego, 
                                                         const ptrdiff_t           CharacterIndex); 
    QUEX_INLINE size_t 
    QUEX_NAME(BufferFiller_Plain_read_characters)(QUEX_NAME(BufferFiller)* alter_ego,
                                                  QUEX_TYPE_CHARACTER*     start_of_buffer, 
                                                  const size_t             N);

    QUEX_INLINE QUEX_NAME(BufferFiller)*
    QUEX_NAME(BufferFiller_Plain_new)(ByteLoader* byte_loader)
    {
        QUEX_NAME(BufferFiller_Plain)*  me = \
             (QUEX_NAME(BufferFiller_Plain)*) \
              QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(BufferFiller_Plain)),
                                             QUEXED(MemoryObjectType_BUFFER_FILLER));
        __quex_assert(me);
        __quex_assert(byte_loader);

        QUEX_NAME(BufferFiller_Plain_construct)(me, byte_loader);

        return &me->base;
    }

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_Plain_construct)(QUEX_NAME(BufferFiller_Plain)* me, 
                                            ByteLoader*                    byte_loader)
    {
        QUEX_NAME(BufferFiller_setup_functions)(&me->base,
                                   QUEX_NAME(BufferFiller_Plain_tell_character_index),
                                   QUEX_NAME(BufferFiller_Plain_seek_character_index), 
                                   QUEX_NAME(BufferFiller_Plain_read_characters),
                                   QUEX_NAME(BufferFiller_Plain_delete_self), 
                                   byte_loader);

        me->start_position        = me->base.byte_loader->tell(me->base.byte_loader);
        me->_last_stream_position = me->start_position;

#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        me->_character_index = 0;
#       endif
    }

    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego) 
    {
        QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
        QUEXED(MemoryManager_free)((void*)me, QUEXED(MemoryObjectType_BUFFER_FILLER));

    }

    QUEX_INLINE ptrdiff_t 
    QUEX_NAME(BufferFiller_Plain_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego) 
    { 
       /* The type cast is necessary, since the function signature needs to 
        * work with the first argument being of base class type. */
       QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;

       __quex_assert(alter_ego != 0x0); 
       __quex_assert(me->base.byte_loader != 0x0); 
       /* Ensure, that the stream position is only influenced by
        *    __read_characters(...) 
        *    __seek_character_index(...)                                             */
       __quex_assert(me->_last_stream_position == me->base.byte_loader->tell(me->base.byte_loader));
#      ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
       return me->_character_index;
#      else
       /* The stream position type is most likely >= size_t >= ptrdiff_t so let the 
        * computation happen with that type, then cast to what needs to be returned. */
       return (ptrdiff_t)(  (me->_last_stream_position - me->start_position) 
                          / (long)sizeof(QUEX_TYPE_CHARACTER));
#      endif
    }

#   if ! defined(QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION)
    /* NOTE: This differs from QuexBuffer_seek(...) in the sense, that it only sets the
     *       stream to a particular position given by a character index. QuexBuffer_seek(..)
     *       sets the _input_p to a particular position.                                      */
    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Plain_seek_character_index)(QUEX_NAME(BufferFiller)* alter_ego, 
                                                       const ptrdiff_t          CharacterIndex) 
    { 
        QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
        long                           avoid_tmp_arg = -1;

        __quex_assert(alter_ego != 0x0); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type. */
        __quex_assert(me->base.byte_loader != 0x0); 

        avoid_tmp_arg =   (long)( ((size_t)CharacterIndex) * sizeof(QUEX_TYPE_CHARACTER)) \
                        + (long)(me->start_position); 

        me->base.byte_loader->seek(me->base.byte_loader, avoid_tmp_arg);
        me->_last_stream_position = me->base.byte_loader->tell(me->base.byte_loader);
    }
#   else
    /* Implementation for 'strange streams', i.e. streams where the input position increase is not
     * necessarily proportional to the amount of read-in characters. Note, that the seek function is
     * the only function that is significantly different for this case.                           */
    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Plain_seek_character_index)(QUEX_NAME(BufferFiller)* alter_ego, 
                                                       const ptrdiff_t          CharacterIndex) 
    { 
        __quex_assert(alter_ego != 0x0); 
        QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
        __quex_assert(me->base.byte_loader != 0x0); 

        if     ( me->_character_index == CharacterIndex ) {
            return;
        }
        else if( me->_character_index < CharacterIndex ) {
            QUEX_NAME(BufferFiller_step_forward_n_characters)(alter_ego, CharacterIndex - me->_character_index);
        }
        else { /* me->_character_index > CharacterIndex */
            me->base.byte_loader->seek(me->base.byte_loader, me->start_position);
#           ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
            me->_last_stream_position = me->base.byte_loader->tell(me->base.byte_loader);
#           endif
            QUEX_NAME(BufferFiller_step_forward_n_characters)(alter_ego, CharacterIndex);
        }
        me->_last_stream_position = me->base.byte_loader->tell(me->base.byte_loader);
    }
#   endif

    QUEX_INLINE size_t   
    QUEX_NAME(BufferFiller_Plain_read_characters)(QUEX_NAME(BufferFiller)*  alter_ego,
                                                  QUEX_TYPE_CHARACTER*      buffer, 
                                                  const size_t              N)  
    { 
        QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
        size_t  ByteN      = (size_t)-1;
        size_t  CharacterN = (size_t)-1;

        __quex_assert(alter_ego); 
        __quex_assert(buffer); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type. */
#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset((uint8_t*)buffer, 0xFF, N * sizeof(QUEX_TYPE_CHARACTER));
#       endif

        __quex_assert(me->base.byte_loader); 
        ByteN = me->base.byte_loader->load(me->base.byte_loader, 
                                           buffer, 
                                           N * sizeof(QUEX_TYPE_CHARACTER));

        if( ByteN % sizeof(QUEX_TYPE_CHARACTER) != 0 ) {
            QUEX_ERROR_EXIT("Error: End of file cuts in the middle a multi-byte character.");
        }

        CharacterN = ByteN / sizeof(QUEX_TYPE_CHARACTER); 

#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        me->_character_index += (ptrdiff_t)CharacterN;
#       endif

        me->_last_stream_position = me->base.byte_loader->tell(me->base.byte_loader);
        return CharacterN;
    }

#   undef TEMPLATED_CLASS

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_PLAIN_I__ */
