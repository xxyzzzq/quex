/* vim: set ft=c:
 * (C) Frank-Rene Schaefer */
#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I

#if ! defined(__QUEX_OPTION_PLAIN_C)

#include <fstream>
#include <sstream>

template <class StreamType> QUEX_INLINE QUEX_TYPE_STREAM_POSITION  ByteLoader_stream_tell(ByteLoader* me);
template <class StreamType> QUEX_INLINE void                       ByteLoader_stream_seek(ByteLoader* me, 
                                                                                          QUEX_TYPE_STREAM_POSITION Pos);
template <class StreamType> QUEX_INLINE size_t                     ByteLoader_stream_load(ByteLoader* me, void* buffer, const size_t ByteN, bool*);
template <class StreamType> QUEX_INLINE void                       ByteLoader_stream_delete_self(ByteLoader* me);
template <class StreamType> QUEX_INLINE bool                       ByteLoader_stream_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B);

template <class StreamType> QUEX_INLINE ByteLoader*
ByteLoader_stream_new(StreamType* sh)
{
    ByteLoader_stream<StreamType>* me;

    if( ! sh ) return (ByteLoader*)0;

    me = (ByteLoader_stream<StreamType>*)QUEXED(MemoryManager_allocate)(sizeof(ByteLoader_stream<StreamType>),
                                                                        E_MemoryObjectType_BYTE_LOADER);

    if( ! me ) return (ByteLoader*)0;

    ByteLoader_stream_construct(me, sh);
    return &me->base;
}

QUEX_INLINE ByteLoader*    
ByteLoader_stream_new_from_file_name(const char* FileName)
{
    std::ifstream*  sh = new std::ifstream(FileName, std::ios_base::binary | std::ios::in);
    ByteLoader*     alter_ego;
    if( ! sh || ! *sh ) {
        return (ByteLoader*)0;
    }
    alter_ego = ByteLoader_stream_new(sh);
    if( ! alter_ego ) {
        return (ByteLoader*)0;
    }
    alter_ego->handle_ownership = E_Ownership_LEXICAL_ANALYZER;
    return alter_ego;
}

template <class StreamType> QUEX_INLINE void
ByteLoader_stream_construct(ByteLoader_stream<StreamType>* me, StreamType* sh)
{
    /* IMPORTANT: input_handle must be set BEFORE call to constructor!
     *            Constructor does call 'tell()'                             */
    me->input_handle = sh;

    ByteLoader_construct(&me->base,
                         ByteLoader_stream_tell<StreamType>,
                         ByteLoader_stream_seek<StreamType>,
                         ByteLoader_stream_load<StreamType>,
                         ByteLoader_stream_delete_self<StreamType>,
                         ByteLoader_stream_compare_handle<StreamType>);
}

template <class StreamType> QUEX_INLINE void
ByteLoader_stream_delete_self(ByteLoader* alter_ego)
{
    ByteLoader_stream<StreamType>* me = (ByteLoader_stream<StreamType>*)alter_ego;

    if( me->input_handle && me->base.handle_ownership == E_Ownership_LEXICAL_ANALYZER ) {
        delete me->input_handle;
    }
    QUEXED(MemoryManager_free)(me, E_MemoryObjectType_BYTE_LOADER);
}

/* The 'char_type' of a stream determines the atomic size of elements which are
 * read from the stream. It is unrelated to QUEX_TYPE_CHARACTER which
 * determines the size of a buffer element.                                  */
template <class StreamType> QUEX_INLINE QUEX_TYPE_STREAM_POSITION    
ByteLoader_stream_tell(ByteLoader* alter_ego)            
{ 
    ByteLoader_stream<StreamType>*       me = (ByteLoader_stream<StreamType>*)alter_ego;
    const QUEX_TYPE_STREAM_POSITION      CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);
    std::streampos                       Position = me->input_handle->tellg();

    return (QUEX_TYPE_STREAM_POSITION)(Position * CharSize); 
}

template <class StreamType> QUEX_INLINE void    
ByteLoader_stream_seek(ByteLoader* alter_ego, QUEX_TYPE_STREAM_POSITION Pos) 
{ 
    ByteLoader_stream<StreamType>*       me = (ByteLoader_stream<StreamType>*)alter_ego;
    const QUEX_TYPE_STREAM_POSITION      CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);
    std::streampos                       Target   = (std::streampos)(Pos / CharSize);

    me->input_handle->clear();                    /* Clear any iostate flag. */
    me->input_handle->seekg(Target); 
}

template <class StreamType> QUEX_INLINE size_t  
ByteLoader_stream_load(ByteLoader*  alter_ego, 
                       void*        buffer, 
                       const size_t ByteN, 
                       bool*        end_of_stream_f) 
{ 
    ByteLoader_stream<StreamType>*    me = (ByteLoader_stream<StreamType>*)alter_ego;
    const QUEX_TYPE_STREAM_POSITION   CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);

    if( ! ByteN ) return (size_t)0;

    me->input_handle->read((typename StreamType::char_type*)buffer, 
                           (std::streamsize)(ByteN / CharSize)); 

    const size_t loaded_char_n = (size_t)(me->input_handle->gcount());

    *end_of_stream_f = me->input_handle->eof();

    if( (! *end_of_stream_f) && me->input_handle->fail() ) {
        throw std::runtime_error("Fatal error during stream reading.");
    }

    /* std::fprintf(stdout, "tell 1 = %i, loaded_char_n = %i\n", (long)(me->input_handle->tellg()), loaded_char_n);*/
    return (size_t)(loaded_char_n * CharSize);
}

template <class StreamType> QUEX_INLINE bool  
ByteLoader_stream_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B) 
/* RETURNS: true  -- if A and B point to the same StreamType object.
 *          false -- else.                                                   */
{ 
    const ByteLoader_stream<StreamType>* A = (ByteLoader_stream<StreamType>*)(alter_ego_A);
    const ByteLoader_stream<StreamType>* B = (ByteLoader_stream<StreamType>*)(alter_ego_B);

    return A->input_handle == B->input_handle;
}

#endif /* __cplusplus                           */
#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I */

