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
        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(buffer._content_character_index_begin == 0); 
        __quex_assert(buffer._memory._end_of_file_p != 0x0); 
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);

        /* Determine the insertion position. */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;

        /* Determine the insertion size. */
        size_t         copy_size = ContentEnd - ContentBegin;
        const size_t   RemainingSize = QuexBuffer_content_back(&buffer) - insertion_p + 1;

        if( copy_size > RemainingSize ) copy_size = RemainingSize;

        const size_t ByteN = copy_size * sizeof(QUEX_TYPE_CHARACTER);
        /* memcpy() might fail if the source and drain domain overlap! */
#       ifdef QUEX_OPTION_ASSERTS 
        if( insertion_p > ContentBegin ) __quex_assert(insertion_p >= ContentBegin + ByteN);
        else                             __quex_assert(insertion_p <= ContentBegin - ByteN);
#       endif
        __QUEX_STD_memcpy(insertion_p, ContentBegin, ByteN);

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, insertion_p + copy_size);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         * We might want to allow to append during lexical analysis. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        return ContentBegin + copy_size;

    }

    inline void*
    CLASS::buffer_fill_region_append_convert(void* ContentBegin, void* ContentEnd)
    /* Appends the content first into a 'raw' buffer and then converts it. This
     * is useful in cases where the 'break' may appear in between characters, or
     * where the statefulness of the converter cannot be controlled.              */
    {
        /* Converting the incoming data using the given converter. */
        TEMPLATED(QuexBufferFiller_Converter)*  filler = (TEMPLATED(QuexBufferFiller_Converter)*)buffer.filler;
        QUEX_TYPE_CHARACTER* remainder_p = 0x0; 

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);

        /* Append the content to the 'raw' buffer */
        remainder_p = QuexBufferFiller_Converter_append_raw_data(filler, ContentBegin, ContentEnd);

        /* Determine the insertion position. */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;

        me->converter->convert(me->converter, 
                               &me->raw_buffer.iterator, me->raw_buffer.end,
                               &insertion_p,             QuexBuffer_content_back(&buffer));

        const size_t ConvertedCharN = insertion_position_after_p - insertion_position_before_p;

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, insertion_p + ConvertedCharN);

        return remainder_p;
    }

    inline void*
    CLASS::buffer_fill_region_append_convert_directly(void* ContentBegin, 
                                                      void* ContentEnd)
    /* Does the conversion directly from the given user buffer to the internal 
     * analyzer buffer. Note, that this can only be used, if it is safe to assume
     * that appended chunks do not break in between the encoding of a single 
     * character.                                                                  */
    {
        TEMPLATED(QuexBufferFiller_Converter)*  filler = (TEMPLATED(QuexBufferFiller_Converter)*)buffer.filler;
        void*  content_begin = ContentBegin;

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);
        
        /* Determine the insertion position. */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;

        me->converter->convert(me->converter, 
                               &content_begin, ContentEnd,
                               &insertion_p,   QuexBuffer_content_back(&buffer));

        return content_begin;
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
