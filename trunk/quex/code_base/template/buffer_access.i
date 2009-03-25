// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 

    inline bool                  
    CLASS::buffer_copy(QUEX_TYPE_CHARACTER* Content, const size_t Size)
    {
        QuexBuffer*           buffer      = &this->buffer;
        size_t                copy_size   = Size;
        const size_t          ContentSize = QuexBuffer_content_size(buffer);
        QUEX_TYPE_CHARACTER*  front       = QuexBuffer_content_front(buffer);

        if( copy_size > ContentSize ) copy_size = ContentSize;
        /* Let us use 'move', because we can never know if the user might want
         * to copy arround content from inside the buffer. 'copy' would assume
         * that the target and source do not overlap.                          */
        __QUEX_STD_memmove(front, Content, copy_size);

        /* Initiate the lexing process */
        this->buffer_prepare(copy_size);

        return copy_size == Size;
    }

    inline bool                  
    CLASS::buffer_append(QUEX_TYPE_CHARACTER* Content, const size_t Size)
    /* NOTE: It is not necessary after a call to this function to do buffer_prepare() */
    {
        QuexBuffer*           buffer = &this->buffer;
        size_t                copy_size     = Size;
        const size_t          RemainingSize =   QuexBuffer_content_back(buffer)
                                              - QuexBuffer_text_end(buffer) + 1;
        QUEX_TYPE_CHARACTER*  text_end      = QuexBuffer_text_end(buffer);

        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(this->buffer._content_character_index_begin == 0); 

        if( copy_size > RemainingSize ) copy_size = RemainingSize;
        /* Let us use 'move', because we can never know if the user might want
         * to copy arround content from inside the buffer. 'copy' would assume
         * that the target and source do not overlap.                          */
        __QUEX_STD_memmove(text_end, Content, copy_size);

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(buffer, text_end + copy_size - 1);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         *
         * (we might want to allow to append during lexical analysis)
         */
        return copy_size == Size;
    }

    inline void
    CLASS::buffer_prepare(const size_t CharacterN)
    {
        QuexBuffer_init(&this->buffer, /* ResetF */ false);
        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&this->buffer, 
                                   QuexBuffer_content_front(&this->buffer) + CharacterN - 1); 
    }

    inline QUEX_TYPE_CHARACTER*  CLASS::buffer_begin()
    { return QuexBuffer_content_front(&this->buffer); }
    
    inline QUEX_TYPE_CHARACTER*  CLASS::buffer_end()
    { return QuexBuffer_content_back(&this->buffer) + 1; }
    
    inline const size_t          CLASS::buffer_size()
    { return QuexBuffer_content_size(&this->buffer); }

    inline QUEX_TYPE_CHARACTER*  CLASS::buffer_text_end()
    { return QuexBuffer_text_end(&this->buffer); }

    inline const size_t          
    CLASS::buffer_distance_to_text_end()
    { return QuexBuffer_distance_input_to_text_end(&this->buffer); }

}
