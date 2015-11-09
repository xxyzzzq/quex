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

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Plain_stomach_byte_n)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_stomach_clear)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE void   
QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE size_t 
QUEX_NAME(BufferFiller_Plain_input_character_load)(QUEX_NAME(BufferFiller)* alter_ego,
                                                   QUEX_TYPE_CHARACTER*     RegionBeginP, 
                                                   const size_t             N);

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_fill_prepare)(QUEX_NAME(BufferFiller)*   alter_ego,
                                           QUEX_TYPE_CHARACTER*       RegionBeginP,
                                           QUEX_TYPE_CHARACTER*       RegionEndP,
                                           void**                     begin_p,
                                           const void**               end_p);

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
    /* A linear relationship between stream position and character index 
     * requires that the input stream is in 'binary mode'. That is, the 
     * stream position is proportional to the number of bytes that lie 
     * behind.                                                               */
    ptrdiff_t   byte_n_per_character = byte_loader && byte_loader->binary_mode_f ? 
                                       (ptrdiff_t)sizeof(QUEX_TYPE_CHARACTER) : -1;
    QUEX_NAME(BufferFiller_setup)(&me->base,
                                  QUEX_NAME(BufferFiller_Plain_input_character_load),
                                  QUEX_NAME(BufferFiller_Plain_stomach_byte_n),
                                  QUEX_NAME(BufferFiller_Plain_stomach_clear),
                                  QUEX_NAME(BufferFiller_Plain_delete_self), 
                                  QUEX_NAME(BufferFiller_Plain_fill_prepare), 
                                  QUEX_NAME(BufferFiller_Plain_fill_finish), 
                                  byte_loader,
                                  byte_n_per_character);
}

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Plain_stomach_byte_n)(QUEX_NAME(BufferFiller)* alter_ego) 
{
    (void)alter_ego;
    return (ptrdiff_t)0;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_stomach_clear)(QUEX_NAME(BufferFiller)* alter_ego) 
{
    (void)alter_ego;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_delete_self)(QUEX_NAME(BufferFiller)* alter_ego) 
{
    QUEX_NAME(BufferFiller_Plain)* me = (QUEX_NAME(BufferFiller_Plain)*)alter_ego;
    ByteLoader_delete(&me->base.byte_loader); 
    QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_BUFFER_FILLER);

}

QUEX_INLINE size_t   
QUEX_NAME(BufferFiller_Plain_input_character_load)(QUEX_NAME(BufferFiller)*  alter_ego,
                                                   QUEX_TYPE_CHARACTER*      RegionBeginP, 
                                                   const size_t              N)  
/* Loads content into a region of memory. Does NOT effect any of the buffer's
 * variables. 
 *
 * AFFECTS: 'filler->base.character_index_next_to_fill'. 
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

    me->base.character_index_next_to_fill += loaded_n;

    return loaded_n;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Plain_fill_prepare)(QUEX_NAME(BufferFiller)*   alter_ego,
                                           QUEX_TYPE_CHARACTER*       RegionBeginP,
                                           QUEX_TYPE_CHARACTER*       RegionEndP,
                                           void**                     begin_p,
                                           const void**               end_p)
{
    (void)alter_ego;

    /* Move-away of passed content in engine's buffer is done by caller. */
    *begin_p = (void*)RegionBeginP;
    *end_p   = (void*)RegionEndP; 
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
