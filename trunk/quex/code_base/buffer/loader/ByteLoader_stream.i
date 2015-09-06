#ifndef QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I
#define QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I
#ifdef __cplusplus

template <class StreamType> QUEX_INLINE QUEX_TYPE_STREAM_POSITION  ByteLoader_stream_tell(ByteLoader* me);
template <class StreamType> QUEX_INLINE void                       ByteLoader_stream_seek(ByteLoader* me, 
                                                                                          QUEX_TYPE_STREAM_POSITION Pos);
template <class StreamType> QUEX_INLINE size_t                     ByteLoader_stream_load(ByteLoader* me, void* buffer, const size_t ByteN);
template <class StreamType> QUEX_INLINE void                       ByteLoader_stream_delete_self(ByteLoader* me);
template <class StreamType> QUEX_INLINE bool                       ByteLoader_stream_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B);

template <class StreamType> QUEX_INLINE ByteLoader*
ByteLoader_stream_new(StreamType* sh)
{
    ByteLoader_stream<StreamType>* me = (ByteLoader_stream<StreamType>*)QUEXED(MemoryManager_allocate)(sizeof(ByteLoader_stream<StreamType>),
                                                                               E_MemoryObjectType_BYTE_LOADER);
    ByteLoader_stream_construct(me, sh);
    return &me->base;
}

template <class StreamType> QUEX_INLINE ByteLoader*    
ByteLoader_stream_new_from_file_name(const char* FileName)
{
    StreamType*  sh = new StreamType(FileName, std::ios_base::binary);
    ByteLoader*  alter_ego;
    if( ! sh ) {
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
    ByteLoader_stream<StreamType>* me = (ByteLoader_stream<StreamType>*)(alter_ego);

    if( me->input_handle && me->base.handle_ownership == E_Ownership_LEXICAL_ANALYZER ) {
        delete me->input_handle;
    }
    QUEXED(MemoryManager_free)(me, E_MemoryObjectType_BYTE_LOADER);
}

/* The 'char_type' of a stream determines the atomic size of elements which are
 * read from the stream. It is unrelated to QUEX_TYPE_CHARACTER which
 * determines the size of a buffer element.                                  */
template <class StreamType> QUEX_INLINE QUEX_TYPE_STREAM_POSITION    
ByteLoader_stream_tell(ByteLoader* me)            
{ 
    const QUEX_TYPE_STREAM_POSITION      CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);
    return (QUEX_TYPE_STREAM_POSITION)(((ByteLoader_stream<StreamType>*)me)->input_handle->tellg() * CharSize); 
}

template <class StreamType> QUEX_INLINE void    
ByteLoader_stream_seek(ByteLoader* me, QUEX_TYPE_STREAM_POSITION Pos) 
{ 
    const QUEX_TYPE_STREAM_POSITION      CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);
    ((ByteLoader_stream<StreamType>*)me)->input_handle->seekg((std::streampos)(Pos / CharSize)); 
}

template <class StreamType> QUEX_INLINE size_t  
ByteLoader_stream_load(ByteLoader* alter_ego, void* buffer, const size_t ByteN) 
{ 
    const QUEX_TYPE_STREAM_POSITION      CharSize = \
         (QUEX_TYPE_STREAM_POSITION)sizeof(typename StreamType::char_type);

    ByteLoader_stream<StreamType>*       me = (ByteLoader_stream<StreamType>*)alter_ego;
    const typename StreamType::pos_type  position_before = me->input_handle->tellg();

    me->input_handle->read((typename StreamType::char_type*)buffer, 
                           (std::streamsize)(ByteN / CharSize)); 

    const size_t loaded_char_n = (size_t)(me->input_handle->gcount());

    if( me->input_handle->eof() && ! me->input_handle->bad() ) {
        me->input_handle->clear();
        /* A position can only be seeked, if it is valid. Interactive input streams
         * may not return a valid stream position, because they have none.           */
        if( position_before != (typename StreamType::pos_type)-1 ) {
            me->input_handle->seekg(
                position_before 
              + (typename StreamType::off_type)(loaded_char_n)
            );
        }
    } else if( me->input_handle->fail() ) {
        throw std::runtime_error("Fatal error during stream reading.");
    }

    /* std::fprintf(stdout, "tell 1 = %i, loaded_char_n = %i\n", (long)(me->input_handle->tellg()), loaded_char_n);*/
    return (size_t)(loaded_char_n * CharSize);
}

template <class StreamType> QUEX_INLINE bool  
ByteLoader_stream_compare_handle(const ByteLoader* alter_ego_A, const ByteLoader* alter_ego_B) 
{ 
    const ByteLoader_stream<StreamType>* A = (ByteLoader_stream<StreamType>*)(alter_ego_A);
    const ByteLoader_stream<StreamType>* B = (ByteLoader_stream<StreamType>*)(alter_ego_B);

    return A->input_handle == B->input_handle;
}

#endif /* __cplusplus                           */
#endif /* QUEX_INCLUDE_GUARD_BYTE_LOADER_STREAM_I */

