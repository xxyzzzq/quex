// -*- C++ -*- vim:set syntax=cpp:
namespace quex { 

    inline QUEX_TYPE_CHARACTER*
    CLASS::buffer_fill_region_append(QUEX_TYPE_CHARACTER* ContentBegin, 
                                     QUEX_TYPE_CHARACTER* ContentEnd)
    /* RETURNS: The position of the first character that could not be copied
     *          into the fill region, because it did not have enough space.
     *          If the whole content was copied, then the return value
     *          is equal to BufferEnd.                                        */
    {
        size_t                copy_size     = ContentEnd - ContentBegin;
        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(buffer._content_character_index_begin == 0); 

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);

        /* Determine the insertion position and copy size. */
        const size_t          RemainingSize =   QuexBuffer_content_back(&buffer)
                                              - QuexBuffer_text_end(&buffer) + 1;
        QUEX_TYPE_CHARACTER*  text_end      = QuexBuffer_text_end(&buffer);

        if( copy_size > RemainingSize ) copy_size = RemainingSize;

        /* Let us use 'move', because we can never know if the user might want
         * to copy arround content from inside the buffer. 'copy' would assume
         * that the target and source do not overlap.                          */
        __QUEX_STD_memmove(text_end, ContentBegin, copy_size * sizeof(QUEX_TYPE_CHARACTER));

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, text_end + copy_size - 1);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         *
         * We might want to allow to append during lexical analysis. */
        return ContentBegin + copy_size;
    }

    inline void
    CLASS::buffer_fill_region_prepare(const size_t CharacterN)
    {
        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);
    }

    inline QUEX_TYPE_CHARACTER*  CLASS::buffer_fill_region_begin()
    { return QuexBuffer_text_end(&buffer); }
    
    inline QUEX_TYPE_CHARACTER*  CLASS::buffer_fill_region_end()
    { return QuexBuffer_content_back(&buffer) + 1; }
    
    inline size_t
    CLASS::buffer_fill_region_size()
    { return buffer_fill_region_end() - buffer_fill_region_begin(); }


    inline void
    CLASS::buffer_fill_region_finish(const size_t CharacterN)
    {
        QuexBuffer_init(&buffer, /* ResetF */ false);
        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, 
                                   QuexBuffer_content_front(&buffer) + CharacterN - 1); 
    }
}
