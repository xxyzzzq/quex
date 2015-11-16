/* (C) Frank-Rene Schaefer */
#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_I

QUEX_INLINE QUEX_TYPE_STREAM_POSITION
ByteLoader_tell(ByteLoader* me);

QUEX_INLINE void
ByteLoader_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Position);

QUEX_INLINE size_t                    
ByteLoader_load(ByteLoader* me, void* begin_p, const size_t N);

QUEX_INLINE void
ByteLoader_construct(ByteLoader* me, 
                     QUEX_TYPE_STREAM_POSITION  (*tell)(ByteLoader* me),
                     void                       (*seek)(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos),
                     size_t                     (*load)(ByteLoader*, void*, const size_t),
                     void                       (*delete_self)(ByteLoader*),
                     bool                       (*compare_handle)(const ByteLoader*, const ByteLoader*))
{
    me->tell           = ByteLoader_tell;
    me->seek           = ByteLoader_seek;
    me->load           = ByteLoader_load;
    me->derived.tell   = tell;
    me->derived.seek   = seek;
    me->derived.load   = load;
    me->delete_self    = delete_self;
    me->compare_handle = compare_handle;
    me->on_nothing     = (bool  (*)(struct ByteLoader_tag*, size_t, size_t))0;

    me->handle_ownership = E_Ownership_EXTERNAL; /* Default                  */
    me->ownership        = E_Ownership_EXTERNAL; /* Default                  */

    me->initial_position = tell(me);

    me->binary_mode_f    = false;                /* Default: 'false' is SAFE */
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION
ByteLoader_tell(ByteLoader* me)
{
    return me->derived.tell(me);
}

QUEX_INLINE void
ByteLoader_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Position)
{
    if( Position < me->initial_position ) return;
    me->derived.seek(me, Position);
}

QUEX_INLINE size_t                    
ByteLoader_load(ByteLoader* me, void* begin_p, const size_t N)
/* RETURNS: != 0, if something could be loaded
 *          == 0, if nothing could be loaded further. End of stream (EOS).   */
{
    size_t loaded_n;
    size_t try_n = 0;
   
    do {
        /* Try to load 'N' bytes.                                            */
        loaded_n  = me->derived.load(me, begin_p, N);
        /* If at least some bytes could be loaded, return 'success'.         */
        if( loaded_n != 0 )         return loaded_n;
        /* If user has no plan for absence of data, return 'failure', EOS.   */
        else if( ! me->on_nothing ) return 0;
        /* If user's on nothing returns 'false' no further attemps to read.  */
        ++try_n;
    } while( me->on_nothing(me, try_n, N) );

    return 0;
}

QUEX_INLINE bool
ByteLoader_is_equivalent(const ByteLoader* A, const ByteLoader* B)
/* RETURNS: true -- if A and B are equivalent.
 *          false -- else.                                                   */
{
    /* If two ByteLoader classes use the same 'load()' function, then they 
     * should not be different. For example, it does not make sense to have
     * two loaders implementing stdandard libraries 'fread()' interface.     
     *
     * Further, it is always safe to return 'false'.                         */
    if( A->load != B->load ) {
        return false;
    }

    /* The 'compare_handle()' function can now safely cast the two pointers
     * to its pointer type.                                                  */
    return A->compare_handle(A, B);
}

QUEX_INLINE void  
ByteLoader_delete(ByteLoader** me)
{
    if( ! *me )                                                 return;
    else if( (*me)->ownership != E_Ownership_LEXICAL_ANALYZER ) return;
    else if( (*me)->delete_self )                               (*me)->delete_self(*me);
    (*me) = (ByteLoader*)0;
}

#include <quex/code_base/buffer/loader/ByteLoader_FILE.i>
#include <quex/code_base/buffer/loader/ByteLoader_stream.i>
#ifdef QUEX_OPTION_POSIX
#   include <quex/buffer/loader/ByteLoader_POSIX.i>    /* (tm) */
#endif
#if 0
#   include <quex/buffer/loader/ByteLoader_FreeRTOS.i> /* (tm) */
#   include <quex/buffer/loader/ByteLoader_PalmOS.i>   /* (tm) */
#endif

#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_I */
