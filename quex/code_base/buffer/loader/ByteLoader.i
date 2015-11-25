/* vim: set ft=c:
 * (C) Frank-Rene Schaefer */
#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_I

QUEX_INLINE QUEX_TYPE_STREAM_POSITION
ByteLoader_tell(ByteLoader* me);

QUEX_INLINE void
ByteLoader_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Position);

QUEX_INLINE size_t                    
ByteLoader_load(ByteLoader* me, void* begin_p, const size_t N, bool* end_of_stream_f);

QUEX_INLINE void
ByteLoader_construct(ByteLoader* me, 
                     QUEX_TYPE_STREAM_POSITION  (*tell)(ByteLoader* me),
                     void                       (*seek)(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos),
                     size_t                     (*load)(ByteLoader*, void*, const size_t, bool*),
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
ByteLoader_load(ByteLoader* me, void* begin_p, const size_t N, bool* end_of_stream_f)
/* RETURNS: != 0, if something could be loaded
 *          == 0, if nothing could be loaded further. End of stream (EOS).   
 *
 * Additionally, 'end_of_stream_f' may hint the end of the stream while still
 * some bytes have been loaded. 
 *
 *    *end_of_stream_f == true  => End of stream has been reached.
 *    *end_of_stream_f == false => No assumption if end of stream ore not.
 *
 * The first case is solely a hint to help the caller to act upon end of stream
 * before actually reading zero bytes. It may spare a unnecessary load-cycle
 * which ends up with no load at all.                                        */
{
    size_t loaded_n;
    size_t try_n = 0;
   
    *end_of_stream_f = false;

    if( ! N ) {
        return 0;
    }

    do {
        /* Try to load 'N' bytes.                                            */
        loaded_n  = me->derived.load(me, begin_p, N, end_of_stream_f);
        if( loaded_n != 0 ) {
            /* If at least some bytes could be loaded, return 'success'.     */
            return loaded_n;
        }
        else if( ! me->on_nothing ) {
            /* No plan for absence of data, return 'failure', EOS.           */
            *end_of_stream_f = true;
            return 0;
        }
        ++try_n;

    } while( me->on_nothing(me, try_n, N) );

    /* If user's on nothing returns 'false' no further attemps to read.      */
    *end_of_stream_f = true;

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
#   include <quex/code_base/buffer/loader/ByteLoader_POSIX.i>    /* (tm) */
#endif
#if 0
#   include <quex/code_base/buffer/loader/ByteLoader_FreeRTOS.i> /* (tm) */
#   include <quex/code_base/buffer/loader/ByteLoader_PalmOS.i>   /* (tm) */
#endif

#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_I */
