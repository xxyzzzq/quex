#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_POSIX_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_POSIX_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/loader/ByteLoader_POSIX>

QUEX_INLINE void                       ByteLoader_POSIX_construct(ByteLoader_POSIX* me, int fd);
QUEX_INLINE QUEX_TYPE_STREAM_POSITION  ByteLoader_POSIX_tell(ByteLoader* me);
QUEX_INLINE void                       ByteLoader_POSIX_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos);
QUEX_INLINE size_t                     ByteLoader_POSIX_load(ByteLoader* me, void* buffer, const size_t ByteN);
QUEX_INLINE void                       ByteLoader_POSIX_delete_self(ByteLoader* me);
QUEX_INLINE bool                       ByteLoader_POSIX_compare_handle(const ByteLoader* alter_ego_A, 
                                                                       const ByteLoader* alter_ego_B);

QUEX_INLINE ByteLoader*    
ByteLoader_POSIX_new(int fd)
{
    ByteLoader_POSIX* me;

    if( fd == -1 ) return (ByteLoader*)0;
    me = (ByteLoader_POSIX*)QUEXED(MemoryManager_allocate)(sizeof(ByteLoader_POSIX),
                                                           E_MemoryObjectType_BYTE_LOADER);
    if( ! me ) return (ByteLoader*)0;
    ByteLoader_POSIX_construct(me, fd);
    return &me->base;
}

QUEX_INLINE ByteLoader*    
ByteLoader_POSIX_new_from_file_name(const char* FileName)
{
    int          fd = open(FileName, O_RDONLY);
    ByteLoader*  alter_ego;

    if( fd == -1 ) {
        return (ByteLoader*)0;
    }
    alter_ego = ByteLoader_POSIX_new(fd);
    if( ! alter_ego ) {
        return (ByteLoader*)0;
    }
    alter_ego->handle_ownership = E_Ownership_LEXICAL_ANALYZER;
    return alter_ego;
}

QUEX_INLINE void
ByteLoader_POSIX_construct(ByteLoader_POSIX* me, int fd)
{
    /* IMPORTANT: fd must be set BEFORE call to constructor!
     *            Constructor does call 'tell()'                             */
    me->fd = fd;

    ByteLoader_construct(&me->base,
                         ByteLoader_POSIX_tell,
                         ByteLoader_POSIX_seek,
                         ByteLoader_POSIX_load,
                         ByteLoader_POSIX_delete_self,
                         ByteLoader_POSIX_compare_handle);

}

QUEX_INLINE void    
ByteLoader_POSIX_delete_self(ByteLoader* alter_ego)
{
    ByteLoader_POSIX* me = (ByteLoader_POSIX*)(alter_ego);

    if( me->fd && me->base.handle_ownership == E_Ownership_LEXICAL_ANALYZER ) {
        close(me->fd);
    }
    QUEXED(MemoryManager_free)(me, E_MemoryObjectType_BYTE_LOADER);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION    
ByteLoader_POSIX_tell(ByteLoader* me)            
{ 
    /* Use 'lseek(current position + 0)' to get the current position.        */
    return (QUEX_TYPE_STREAM_POSITION)lseek(((ByteLoader_POSIX*)me)->fd, 0, SEEK_CUR); 
}

QUEX_INLINE void    
ByteLoader_POSIX_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos) 
{ lseek(((ByteLoader_POSIX*)me)->fd, (long)Pos, SEEK_SET); }

QUEX_INLINE size_t  
ByteLoader_POSIX_load(ByteLoader* me, void* buffer, const size_t ByteN) 
{ 
    int n = read(((ByteLoader_POSIX*)me)->fd, buffer, ByteN); 
    printf("n=%i;\n", (int)n);
    return n;
}

QUEX_INLINE bool  
ByteLoader_POSIX_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B) 
/* RETURNS: true  -- if A and B point to the same POSIX object.
 *          false -- else.                                                   */
{ 
    const ByteLoader_POSIX* A = (ByteLoader_POSIX*)(alter_ego_A);
    const ByteLoader_POSIX* B = (ByteLoader_POSIX*)(alter_ego_B);

    return A->fd == B->fd;
}

#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_POSIX_I */

