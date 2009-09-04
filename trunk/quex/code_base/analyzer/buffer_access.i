/* -*- C++ -*- vim:set syntax=cpp:
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_BUFFER_ACCESS_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_BUFFER_ACCESS_I__  */


namespace quex { 


    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_append)(__QUEX_SETTING_THIS_POINTER
                                                                QUEX_TYPE_CHARACTER* ContentBegin, 
                                                                QUEX_TYPE_CHARACTER* ContentEnd)
    /* RETURNS: The position of the first character that could not be copied
     *          into the fill region, because it did not have enough space.
     *          If the whole content was copied, then the return value
     *          is equal to BufferEnd.                                        */
    {
        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(buffer._content_character_index_begin == 0); 
        __quex_assert(buffer._memory._end_of_file_p != 0x0); 
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(ContentBegin, ContentEnd);

        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);

        /* Determine the insertion position. */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;

        const size_t CopiedByteN = MemoryManager_insert((uint8_t*)insertion_p,  
                                                        (uint8_t*)(QuexBuffer_content_back(&buffer) + 1),
                                                        (uint8_t*)ContentBegin, 
                                                        (uint8_t*)ContentEnd);
        const size_t CopiedCharN = CopiedByteN / sizeof(QUEX_TYPE_CHARACTER);

        if( buffer._byte_order_reversion_active_f ) 
            __Buffer_reverse_byte_order(buffer._memory._end_of_file_p, insertion_p + CopiedCharN);

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QuexBuffer_end_of_file_set(&buffer, insertion_p + CopiedCharN);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         * We might want to allow to append during lexical analysis. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        return ContentBegin + CopiedCharN;
    }

    QUEX_INLINE uint8_t*
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_append_conversion)(__QUEX_SETTING_THIS_POINTER
                                                                           uint8_t* ContentBegin, uint8_t* ContentEnd)
    /* Appends the content first into a 'raw' buffer and then converts it. This
     * is useful in cases where the 'break' may appear in between characters, or
     * where the statefulness of the converter cannot be controlled.              */
    {
        /* The buffer filler for direct memory handling must be of a 'void' specialization. */
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);

        /* (1) Append the content to the 'raw' buffer. */
        /*     -- Move away passed buffer content.                                      */
        QuexBufferFiller_Converter_move_away_passed_content(filler);

        const size_t CopiedByteN = MemoryManager_insert(filler->raw_buffer.end, 
                                                        filler->raw_buffer.memory_end,
                                                        (uint8_t*)ContentBegin, 
                                                        (uint8_t*)ContentEnd);

        filler->raw_buffer.end += CopiedByteN;

        /* (2) Convert data from the 'raw' buffer into the analyzer buffer.             */

        /*     -- Move away passed buffer content.                                      */
        QuexBuffer_move_away_passed_content(&buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;
        filler->converter->convert(filler->converter, 
                                   &filler->raw_buffer.iterator, filler->raw_buffer.end,
                                   &insertion_p,                 QuexBuffer_content_back(&buffer) + 1);

        if( buffer._byte_order_reversion_active_f ) 
            __Buffer_reverse_byte_order(buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(buffer._memory._end_of_file_p, insertion_p);

        QuexBuffer_end_of_file_set(&buffer, insertion_p);

        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        return ContentBegin + CopiedByteN;
    }

    QUEX_INLINE uint8_t*
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_append_conversion_direct)(__QUEX_SETTING_THIS_POINTER
                                                                                  uint8_t* ContentBegin, 
                                                                                  uint8_t* ContentEnd)
    /* Does the conversion directly from the given user buffer to the internal 
     * analyzer buffer. Note, that this can only be used, if it is safe to assume
     * that appended chunks do not break in between the encoding of a single 
     * character.                                                                  */
    {
        /* The buffer filler for direct memory handling must be of a 'void' specialization. */
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);

        /*     -- Move away passed buffer content.                                      */
        QuexBuffer_move_away_passed_content(&buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p   = buffer._memory._end_of_file_p;
        uint8_t*              content_begin = ContentBegin;
        filler->converter->convert(filler->converter, 
                                   &content_begin, ContentEnd,
                                   &insertion_p,  QuexBuffer_content_back(&buffer) + 1);

        if( buffer._byte_order_reversion_active_f ) 
            __Buffer_reverse_byte_order(buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(buffer._memory._end_of_file_p, insertion_p);

        QuexBuffer_end_of_file_set(&buffer, insertion_p);

        QUEX_BUFFER_ASSERT_CONSISTENCY(&buffer);
        /* 'content_begin' has been adapted by the converter. */
        return content_begin;
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_prepare)(__QUEX_SETTING_THIS_POINTER)
    {
        /* Move away unused passed buffer content. */
        QuexBuffer_move_away_passed_content(&buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_begin)(__QUEX_SETTING_THIS_POINTER)
    { 
        return QuexBuffer_text_end(&buffer); 
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_end)(__QUEX_SETTING_THIS_POINTER)
    { 
        return QuexBuffer_content_back(&buffer) + 1; 
    }

    QUEX_INLINE size_t
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_size)(__QUEX_SETTING_THIS_POINTER)
    { 
        return buffer_fill_region_end() - buffer_fill_region_begin(); 
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_fill_region_finish)(__QUEX_SETTING_THIS_POINTER
                                                                const size_t CharacterN)
    {
        __quex_assert(buffer._memory._end_of_file_p + CharacterN <= buffer._memory._back);

        /* We assume that the content from '_end_of_file_p' to '_end_of_file_p + CharacterN'
         * has been filled with data.                                                        */
        if( buffer._byte_order_reversion_active_f ) 
            __Buffer_reverse_byte_order(buffer._memory._end_of_file_p, 
                                        buffer._memory._end_of_file_p + CharacterN);

        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(buffer._memory._end_of_file_p, 
                                                buffer._memory._end_of_file_p + CharacterN);

        /* When lexing directly on the buffer, the end of file pointer is always set.        */
        QuexBuffer_end_of_file_set(&buffer, 
                                   buffer._memory._end_of_file_p + CharacterN); 
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_conversion_fill_region_prepare)(__QUEX_SETTING_THIS_POINTER
                                                                            ) 
    {
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;

        /* It is always assumed that the buffer filler w/ direct buffer accesss
         * is a converter. Now, move away past content in the raw buffer.       */
        QuexBufferFiller_Converter_move_away_passed_content(filler);
    }

    QUEX_INLINE uint8_t*  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_conversion_fill_region_begin)(__QUEX_SETTING_THIS_POINTER)
    { 
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;
        return filler->raw_buffer.end;
    }
    
    QUEX_INLINE uint8_t*  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_conversion_fill_region_end)(__QUEX_SETTING_THIS_POINTER)
    { 
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;

        return filler->raw_buffer.memory_end;
    }
    
    QUEX_INLINE size_t
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_conversion_fill_region_size)(__QUEX_SETTING_THIS_POINTER)
    { 
        return buffer_conversion_fill_region_end() - buffer_conversion_fill_region_begin(); 
    }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_conversion_fill_region_finish)(__QUEX_SETTING_THIS_POINTER
                                                                           const size_t  ByteN)
    {
        QuexBufferFiller_Converter<void>*  filler = (QuexBufferFiller_Converter<void>*)buffer.filler;

        filler->raw_buffer.end += ByteN;

        /*     -- Move away passed buffer content.                                      */
        QuexBuffer_move_away_passed_content(&buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p = buffer._memory._end_of_file_p;
        filler->converter->convert(filler->converter, 
                                   &filler->raw_buffer.iterator, filler->raw_buffer.end,
                                   &insertion_p,                 QuexBuffer_content_back(&buffer) + 1);

        if( buffer._byte_order_reversion_active_f ) 
            __Buffer_reverse_byte_order(buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(buffer._memory._end_of_file_p, insertion_p);

        QuexBuffer_end_of_file_set(&buffer, insertion_p);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_lexeme_start_pointer_get)(__QUEX_SETTING_THIS_POINTER) 
    { return buffer._lexeme_start_p; }

    QUEX_INLINE void
    QUEX_MEMFUNC(QUEX_TYPE_ANALYZER, buffer_input_pointer_set)(__QUEX_SETTING_THIS_POINTER
                                                               QUEX_TYPE_CHARACTER* Adr)
    { buffer._input_p = Adr; }

}

