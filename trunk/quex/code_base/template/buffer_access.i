// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 

    inline bool                  
    CLASS::buffer_copy(QUEX_CHARACTER_TYPE* Content, const size_t Size)
    {
        QuexBuffer*           buffer      = &this->buffer;
        size_t                copy_size   = Size;
        const size_t          ContentSize = QuexBuffer_content_size(buffer);
        QUEX_CHARACTER_TYPE*  front       = QuexBuffer_content_front(buffer);

        if( copy_size > ContentSize ) copy_size = ContentSize;
        __QUEX_STD_memcpy(front, Content, copy_size);

        /* (*) If end of file has been reached, then the 'end of file' pointer needs to be set*/
        if( copy_size != Size ) QuexBuffer_end_of_file_set(buffer, front + copy_size);
        else                    QuexBuffer_end_of_file_unset(buffer);

        buffer->_content_first_character_index = 0;
        buffer->_input_p        = 0;
        buffer->_lexeme_start_p = 0;

        return copy_size == Size;
    }

    inline bool                  
    CLASS::buffer_append(QUEX_CHARACTER_TYPE* Content, const size_t Size)
    {
        QuexBuffer*           buffer = &this->buffer;
        size_t                copy_size     = Size;
        const size_t          RemainingSize =   QuexBuffer_content_back(buffer)
                                              - QuexBuffer_text_end(buffer) + 1;
        QUEX_CHARACTER_TYPE*  text_end      = QuexBuffer_text_end(buffer);

        if( copy_size > RemainingSize ) copy_size = RemainingSize;
        __QUEX_STD_memcpy(text_end, Content, copy_size);

        /* (*) If end of file has been reached, then the 'end of file' pointer needs to be set */
        if( copy_size != Size ) QuexBuffer_end_of_file_set(buffer, text_end + copy_size);
        else                    QuexBuffer_end_of_file_unset(buffer);

        buffer->_content_first_character_index = 0;
        /* No change to input_p and lexeme_start_p 
         * buffer->_input_p        = 0;
         * buffer->_lexeme_start_p = 0;            */
        return copy_size == Size;
    }

    inline QUEX_CHARACTER_TYPE*  CLASS::buffer_begin()
    { return QuexBuffer_content_front(&this->buffer); }
    
    inline QUEX_CHARACTER_TYPE*  CLASS::buffer_end()
    { return QuexBuffer_content_back(&this->buffer) + 1; }
    
    inline const size_t          CLASS::buffer_size()
    { return QuexBuffer_content_size(&this->buffer); }

    inline QUEX_CHARACTER_TYPE*  CLASS::buffer_text_end()
    { return QuexBuffer_text_end((QuexBuffer*)this); }
}
