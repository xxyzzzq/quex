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
        __quex_assert(buffer._memory._end_of_file_p != 0x0); 
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);

        /* Determine the insertion position and copy size. */
        QUEX_TYPE_CHARACTER*  text_end      =   buffer._memory._end_of_file_p;
        const size_t          RemainingSize =   QuexBuffer_content_back(&buffer)
                                              - text_end + 1;

        if( copy_size > RemainingSize ) copy_size = RemainingSize;

        const size_t ByteN = copy_size * sizeof(QUEX_TYPE_CHARACTER);
        /* memcpy() might fail if the source and drain domain overlap! */
#       ifdef QUEX_OPTION_ASSERTS 
        if( text_end > ContentBegin ) __quex_assert(text_end >= ContentBegin + ByteN);
        else                          __quex_assert(text_end <= ContentBegin - ByteN);
#       endif
        __QUEX_STD_memcpy(text_end, ContentBegin, ByteN);

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, text_end + copy_size);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         *
         * We might want to allow to append during lexical analysis. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        return ContentBegin + copy_size;
    }

    inline QUEX_TYPE_CHARACTER*
    CLASS::buffer_fill_region_prepare()
    {
        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);
        return QuexBuffer_text_end(&buffer); 
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
        __quex_assert(buffer._memory._end_of_file_p + CharacterN <= buffer._memory._back);
        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, 
                                   buffer._memory._end_of_file_p + CharacterN); 
    }

    inline QUEX_TYPE_CHARACTER*  
    CLASS::buffer_lexeme_start_pointer_get() 
    { return buffer._lexeme_start_p; }

    inline void
    CLASS::buffer_input_pointer_set(QUEX_TYPE_CHARACTER* Adr)
    { buffer._input_p = Adr; }

}
