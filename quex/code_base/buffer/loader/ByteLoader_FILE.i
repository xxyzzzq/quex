#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_FILE_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_FILE_I

#include <quex/code_base/MemoryManager>

QUEX_INLINE void                       ByteLoader_FILE_construct(ByteLoader_FILE* me, __QUEX_STD_FILE* fh);
QUEX_INLINE QUEX_TYPE_STREAM_POSITION  ByteLoader_FILE_tell(ByteLoader* me);
QUEX_INLINE void                       ByteLoader_FILE_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos);
QUEX_INLINE size_t                     ByteLoader_FILE_load(ByteLoader* me, void* buffer, const size_t ByteN);
QUEX_INLINE void                       ByteLoader_FILE_delete_self(ByteLoader* me);
QUEX_INLINE bool                       ByteLoader_FILE_compare_handle(const ByteLoader* alter_ego_A, 
                                                                      const ByteLoader* alter_ego_B);

QUEX_INLINE ByteLoader*    
ByteLoader_FILE_new(FILE* fh)
{
    ByteLoader_FILE* me = (ByteLoader_FILE*)QUEXED(MemoryManager_allocate)(
                                                   sizeof(ByteLoader_FILE),
                                                   E_MemoryObjectType_BYTE_LOADER);
    if( ! me ) {
        return (ByteLoader*)0;
    }
    ByteLoader_FILE_construct(me, fh);
    return &me->base;
}

QUEX_INLINE ByteLoader*    
ByteLoader_FILE_new_from_file_name(const char* FileName)
{
    __QUEX_STD_FILE* fh = fopen(FileName, "rb");
    ByteLoader*      alter_ego;
    if( ! fh ) {
        return (ByteLoader*)0;
    }
    alter_ego = ByteLoader_FILE_new(fh);
    if( ! alter_ego ) {
        return (ByteLoader*)0;
    }
    alter_ego->handle_ownership = E_Ownership_LEXICAL_ANALYZER;
    return alter_ego;
}

QUEX_INLINE void
ByteLoader_FILE_construct(ByteLoader_FILE* me, __QUEX_STD_FILE* fh)
{
    /* IMPORTANT: input_handle must be set BEFORE call to constructor!
     *            Constructor does call 'tell()'                             */
    me->input_handle = fh;

    ByteLoader_construct(&me->base,
                         ByteLoader_FILE_tell,
                         ByteLoader_FILE_seek,
                         ByteLoader_FILE_load,
                         ByteLoader_FILE_delete_self,
                         ByteLoader_FILE_compare_handle);

}

QUEX_INLINE void    
ByteLoader_FILE_delete_self(ByteLoader* alter_ego)
{
    ByteLoader_FILE* me = (ByteLoader_FILE*)(alter_ego);

    if( me->input_handle && me->base.handle_ownership == E_Ownership_LEXICAL_ANALYZER ) {
        fclose(me->input_handle);
    }
    QUEXED(MemoryManager_free)(me, E_MemoryObjectType_BYTE_LOADER);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION    
ByteLoader_FILE_tell(ByteLoader* me)            
{ return (QUEX_TYPE_STREAM_POSITION)ftell(((ByteLoader_FILE*)me)->input_handle); }

QUEX_INLINE void    
ByteLoader_FILE_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos) 
{ fseek(((ByteLoader_FILE*)me)->input_handle, (long)Pos, SEEK_SET); }

QUEX_INLINE size_t  
ByteLoader_FILE_load(ByteLoader* me, void* buffer, const size_t ByteN) 
{ return fread(buffer, 1, ByteN, ((ByteLoader_FILE*)me)->input_handle); }

QUEX_INLINE bool  
ByteLoader_FILE_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B) 
{ 
    const ByteLoader_FILE* A = (ByteLoader_FILE*)(alter_ego_A);
    const ByteLoader_FILE* B = (ByteLoader_FILE*)(alter_ego_B);

    return A->input_handle == B->input_handle;
}

#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_FILE_I */
