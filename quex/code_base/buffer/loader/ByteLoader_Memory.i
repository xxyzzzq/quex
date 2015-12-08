/* vim: set ft=c:
 * (C) Frank-Rene Schaefer */
#ifndef  __QUEX_INCLUDE_GUARD__BUFFER__LOADER__BYTE_LOADER_Memory_I
#define  __QUEX_INCLUDE_GUARD__BUFFER__LOADER__BYTE_LOADER_Memory_I

#include <quex/code_base/MemoryManager>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void                       QUEX_NAME(ByteLoader_Memory_construct)(QUEX_NAME(ByteLoader_Memory)* me,
                                                                              const uint8_t*                BeginP,
                                                                              const uint8_t*                EndP);
QUEX_INLINE QUEX_TYPE_STREAM_POSITION  QUEX_NAME(ByteLoader_Memory_tell)(QUEX_NAME(ByteLoader)* me);
QUEX_INLINE void                       QUEX_NAME(ByteLoader_Memory_seek)(QUEX_NAME(ByteLoader)*    me, 
                                                                         QUEX_TYPE_STREAM_POSITION Pos);
QUEX_INLINE size_t                     QUEX_NAME(ByteLoader_Memory_load)(QUEX_NAME(ByteLoader)* me, 
                                                                         void*                  buffer, 
                                                                         const size_t           ByteN, 
                                                                         bool*                  end_of_stream_f);
QUEX_INLINE void                       QUEX_NAME(ByteLoader_Memory_delete_self)(QUEX_NAME(ByteLoader)* me);
QUEX_INLINE bool                       QUEX_NAME(ByteLoader_Memory_compare_handle)(const QUEX_NAME(ByteLoader)* alter_ego_A, 
                                                                                   const QUEX_NAME(ByteLoader)* alter_ego_B);

QUEX_INLINE QUEX_NAME(ByteLoader)*    
QUEX_NAME(ByteLoader_Memory_new)(const uint8_t*  BeginP,
                                 const uint8_t*  EndP)
{
    QUEX_NAME(ByteLoader_Memory)* me;
   
    if( ! BeginP || ! EndP ) return (QUEX_NAME(ByteLoader)*)0;

    me = (QUEX_NAME(ByteLoader_Memory)*)QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(ByteLoader_Memory)),
                                                                       E_MemoryObjectType_BYTE_LOADER);
    if( ! me ) return (QUEX_NAME(ByteLoader)*)0;

    QUEX_NAME(ByteLoader_Memory_construct)(me, BeginP, EndP);

    return &me->base;
}

QUEX_INLINE void
QUEX_NAME(ByteLoader_Memory_construct)(QUEX_NAME(ByteLoader_Memory)* me, 
                                       const uint8_t*                BeginP,
                                       const uint8_t*                EndP)
{
    __quex_assert(EndP >= BeginP);
    me->byte_array.begin_p  = BeginP;
    me->byte_array.position = BeginP;
    me->byte_array.end_p    = EndP;
    QUEX_NAME(ByteLoader_construct)(&me->base,
                         QUEX_NAME(ByteLoader_Memory_tell),
                         QUEX_NAME(ByteLoader_Memory_seek),
                         QUEX_NAME(ByteLoader_Memory_load),
                         QUEX_NAME(ByteLoader_Memory_delete_self),
                         QUEX_NAME(ByteLoader_Memory_compare_handle));
    me->base.binary_mode_f = true;
}

QUEX_INLINE void    
QUEX_NAME(ByteLoader_Memory_delete_self)(QUEX_NAME(ByteLoader)* alter_ego)
{
    /* NOTE: The momory's ownership remains in the hand of the one who
     *       constructed this object.                                        */
    QUEX_NAME(ByteLoader_Memory)* me = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego);

    QUEXED(MemoryManager_free)(me, E_MemoryObjectType_BYTE_LOADER);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION    
QUEX_NAME(ByteLoader_Memory_tell)(QUEX_NAME(ByteLoader)* alter_ego)            
{ 
    const QUEX_NAME(ByteLoader_Memory)* me = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego);

    return me->byte_array.position - me->byte_array.begin_p;
}

QUEX_INLINE void    
QUEX_NAME(ByteLoader_Memory_seek)(QUEX_NAME(ByteLoader)* alter_ego, QUEX_TYPE_STREAM_POSITION Pos) 
{ 
    QUEX_NAME(ByteLoader_Memory)* me = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego);

    if( Pos > me->byte_array.end_p -  me->byte_array.begin_p ) return;
    me->byte_array.position = &me->byte_array.begin_p[(ptrdiff_t)Pos];
}

QUEX_INLINE size_t  
QUEX_NAME(ByteLoader_Memory_load)(QUEX_NAME(ByteLoader)* alter_ego, 
                                void*                    buffer, 
                                const size_t             ByteN, 
                                bool*                    end_of_stream_f) 
{ 
    QUEX_NAME(ByteLoader_Memory)* me = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego);
    const ptrdiff_t               Remaining = me->byte_array.end_p - me->byte_array.position;
    ptrdiff_t                     copy_n;

    if( Remaining < ByteN ) { copy_n = Remaining; *end_of_stream_f = true; }
    else                    { copy_n = ByteN; } 

    __QUEX_STD_memcpy((void*)buffer, (void*)me->byte_array.position, copy_n);
    me->byte_array.position += copy_n;
    return copy_n;
}

QUEX_INLINE bool  
QUEX_NAME(ByteLoader_Memory_compare_handle)(const QUEX_NAME(ByteLoader)* alter_ego_A, 
                                            const QUEX_NAME(ByteLoader)* alter_ego_B) 
/* RETURNS: true  -- if A and B point to the same Memory object.
 *          false -- else.                                                   */
{ 
    const QUEX_NAME(ByteLoader_Memory)* A = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego_A);
    const QUEX_NAME(ByteLoader_Memory)* B = (QUEX_NAME(ByteLoader_Memory)*)(alter_ego_B);

    return    A->byte_array.begin_p  == B->byte_array.begin_p
           && A->byte_array.end_p    == B->byte_array.end_p
           && A->byte_array.position == B->byte_array.position;
}

QUEX_NAMESPACE_MAIN_CLOSE

#endif /*  __QUEX_INCLUDE_GUARD__BUFFER__LOADER__BYTE_LOADER_Memory_I */
