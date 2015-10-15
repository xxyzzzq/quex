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
#include <quex/code_base/buffer/filler/BufferFiller>
#include <quex/code_base/MemoryManager>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(BufferFiller_Plain_construct)(QUEX_NAME(BufferFiller_Plain)*, ByteLoader* byte_loader);

QUEX_INLINE void   
QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
QUEX_NAME(BufferFiller_Plain_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE bool   
QUEX_NAME(BufferFiller_Plain_seek_character_index)(QUEX_NAME(BufferFiller)*  alter_ego, 
                                                   const QUEX_TYPE_STREAM_POSITION  CharacterIndex); 
QUEX_INLINE size_t 
QUEX_NAME(BufferFiller_Plain_input_character_load)(QUEX_NAME(BufferFiller)* alter_ego,
                                                   QUEX_TYPE_CHARACTER*     RegionBeginP, 
                                                   const size_t             N);

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_fill_prepare)(QUEX_NAME(Buffer)*  me,
                                           void**              begin_p,
                                           const void**        end_p);

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Plain_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                          QUEX_TYPE_CHARACTER*       insertion_p,
                                          const QUEX_TYPE_CHARACTER* BufferEnd,
                                          const void*                ContentEnd);

QUEX_INLINE QUEX_NAME(BufferFiller)*
QUEX_NAME(BufferFiller_Plain_new)(ByteLoader* byte_loader)
{
    QUEX_NAME(BufferFiller_Plain)*  me = \
         (QUEX_NAME(BufferFiller_Plain)*) \
          QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(BufferFiller_Plain)),
                                         E_MemoryObjectType_BUFFER_FILLER);
    __quex_assert(me);
    /* __quex_assert(byte_loader); not for manual filling. */

    QUEX_NAME(BufferFiller_Plain_construct)(me, byte_loader);

    return &me->base;
}

QUEX_INLINE void
QUEX_NAME(BufferFiller_Plain_construct)(QUEX_NAME(BufferFiller_Plain)* me, 
                                        ByteLoader*                    byte_loader)
{
    QUEX_NAME(BufferFiller_setup)(&me->base,
                                  QUEX_NAME(BufferFiller_Plain_tell_character_index),
                                  QUEX_NAME(BufferFiller_Plain_seek_character_index), 
                                  QUEX_NAME(BufferFiller_Plain_input_character_load),
                                  QUEX_NAME(BufferFiller_Plain_delete_self), 
                                  QUEX_NAME(BufferFiller_Plain_fill_prepare), 
                                  QUEX_NAME(BufferFiller_Plain_fill_finish), 
                                  byte_loader);

#   ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
    me->next_to_load_character_index = 0;
#   endif
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego) 
{
    QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
    ByteLoader_delete(&me->base.byte_loader); 
    QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_BUFFER_FILLER);

}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
QUEX_NAME(BufferFiller_Plain_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego) 
{ 
   /* The type cast is necessary, since the function signature needs to 
    * work with the first argument being of base class type. */
   QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;

   __quex_assert(alter_ego); 
   __quex_assert(me->base.byte_loader); 

   /* Ensure, that the stream position is only influenced by
    *    __input_character_read(...) 
    *    __seek_character_index(...)                                             */
   return me->next_to_load_character_index;
}

QUEX_INLINE bool 
QUEX_NAME(BufferFiller_Plain_seek_character_index)(QUEX_NAME(BufferFiller)*         alter_ego, 
                                                   const QUEX_TYPE_STREAM_POSITION  CharacterIndex) 
/* BufferFiller's seek sets the input position for the next character load in
 * the stream. That is, it adapts:
 *
 *     'next_to_convert_character_index = CharacterIndex' 
 *
 * and the byte loader is brought into a position so that this will happen.  
 *
 * RETURNS: true upon success, false else.                                   */
{ 
    QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
    QUEX_TYPE_STREAM_POSITION      backup_byte_pos;
    QUEX_TYPE_STREAM_POSITION      target_byte_pos;
    QUEX_TYPE_STREAM_POSITION      backup_next_to_load_character_index;

    if( me->next_to_load_character_index == CharacterIndex ) return true;

    backup_byte_pos = me->base.byte_loader->tell(me->base.byte_loader);
    
    if( me->base.byte_loader->binary_mode_f ) {
        target_byte_pos =   CharacterIndex * sizeof(QUEX_TYPE_CHARACTER)
                          + me->base.byte_loader->initial_position;

        me->base.byte_loader->seek(me->base.byte_loader, target_byte_pos);
        if( me->base.byte_loader->tell(me->base.byte_loader) != target_byte_pos ) {
            me->base.byte_loader->seek(me->base.byte_loader, backup_byte_pos);
            return false;
        }
        me->next_to_load_character_index =   (target_byte_pos - me->base.byte_loader->initial_position)
                                           / sizeof(QUEX_TYPE_CHARACTER);
        return true;
    }

    /* Start at known position; step until 'CharacterIndex' is reached.  */
    me->base.byte_loader->seek(me->base.byte_loader, 
                               me->base.byte_loader->initial_position);
    if(    me->base.byte_loader->tell(me->base.byte_loader) 
        != me->base.byte_loader->initial_position ) {
        me->base.byte_loader->seek(me->base.byte_loader, backup_byte_pos);
        return false;
    }

    backup_next_to_load_character_index = me->next_to_load_character_index;
    me->next_to_load_character_index    = 0;
    /* 'step_forward' calls 'BufferFiller_Plain_input_character_load()' 
     * which increments 'next_to_load_character_index'.                  */
    if( ! QUEX_NAME(BufferFiller_step_forward_n_characters)(alter_ego,
                                                            (ptrdiff_t)CharacterIndex) ) {
        me->next_to_load_character_index = backup_next_to_load_character_index;
        me->base.byte_loader->seek(me->base.byte_loader, backup_byte_pos);
        return false;
    }
    return true;
}

QUEX_INLINE size_t   
QUEX_NAME(BufferFiller_Plain_input_character_load)(QUEX_NAME(BufferFiller)*  alter_ego,
                                                   QUEX_TYPE_CHARACTER*      RegionBeginP, 
                                                   const size_t              N)  
/* Loads content into a region of memory. Does NOT effect any of the buffer's
 * variables. 
 *
 * AFFECTS: 'filler->next_to_load_character_index'. 
 *          => may be used to seek through non-linear input streams.
 *
 * RETURNS: Number of loaded characters into the given region.               */
{ 
    QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
    size_t                         loaded_byte_n = (size_t)-1;
    size_t                         loaded_n;

    __quex_assert(alter_ego); 
    __quex_assert(RegionBeginP); 
    __quex_assert(me->base.byte_loader); 
    /* NOT: QUEX_IF_ASSERTS_poison(RegionBeginP, &RegionBeginP[N]);
     * The buffer must remain intact, in case that not all is loaded.        */

    loaded_byte_n = me->base.byte_loader->load(me->base.byte_loader, 
                                               RegionBeginP, 
                                               N * sizeof(QUEX_TYPE_CHARACTER));

    if( loaded_byte_n % sizeof(QUEX_TYPE_CHARACTER) ) {
        QUEX_ERROR_EXIT("Error: End of file cuts in the middle a multi-byte character.");
    }
    loaded_n = loaded_byte_n / sizeof(QUEX_TYPE_CHARACTER);

    me->next_to_load_character_index += loaded_n;

    return loaded_n;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_fill_prepare)(QUEX_NAME(Buffer)*  buffer,
                                           void**              begin_p,
                                           const void**        end_p)
{
    /* Move-away of passed content in engine's buffer is done by caller. */
    *begin_p = (void*)QUEX_NAME(Buffer_text_end)(buffer);
    *end_p   = (void*)&QUEX_NAME(Buffer_content_back)(buffer)[1];
}

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Plain_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                          QUEX_TYPE_CHARACTER*       insertion_p,
                                          const QUEX_TYPE_CHARACTER* BufferEnd,
                                          const void*                FilledEndP)
{
    const QUEX_TYPE_CHARACTER*  EndP = (const QUEX_TYPE_CHARACTER*)FilledEndP;
    (void)alter_ego;
    (void)BufferEnd;
    __quex_assert(EndP >= insertion_p);
    __quex_assert(EndP <= BufferEnd);

    /* Copying of content is done, already, by caller.                       */
    /* Inserted number of characters = End - Begin.                          */
    return (ptrdiff_t)(EndP - insertion_p);
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/filler/BufferFiller.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_PLAIN_I__ */
