/* -*- C++ -*- vim:set syntax=cpp:
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_BUFFER_ACCESS_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_BUFFER_ACCESS_I__  */

#include <quex/code_base/buffer/asserts>
#include <quex/code_base/buffer/Buffer>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_FUNC(buffer_fill_region_append)(QUEX_TYPE_ANALYZER*    me, 
                                            QUEX_TYPE_CHARACTER*   ContentBegin, 
                                            QUEX_TYPE_CHARACTER*   ContentEnd)
    /* RETURNS: The position of the first character that could not be copied
     *          into the fill region, because it did not have enough space.
     *          If the whole content was copied, then the return value
     *          is equal to BufferEnd.                                        */
    {
        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(me->buffer._content_character_index_begin == 0); 
        __quex_assert(me->buffer._memory._end_of_file_p != 0x0); 
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(ContentBegin, ContentEnd);

        /* Move away unused passed buffer content. */
        QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);

        /* Determine the insertion position. */
        QUEX_TYPE_CHARACTER*  insertion_p = me->buffer._memory._end_of_file_p;

        const size_t CopiedByteN = QUEX_NAME(MemoryManager_insert)((uint8_t*)insertion_p,  
                                            (uint8_t*)(QUEX_NAME(Buffer_content_back)(&me->buffer) + 1),
                                            (uint8_t*)ContentBegin, 
                                            (uint8_t*)ContentEnd);
        const size_t CopiedCharN = CopiedByteN / sizeof(QUEX_TYPE_CHARACTER);

        if( me->buffer._byte_order_reversion_active_f ) 
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, 
                                                 insertion_p + CopiedCharN);

        /* When lexing directly on the buffer, the end of file pointer is always set. */
        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, 
                                          insertion_p + CopiedCharN);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         * We might want to allow to append during lexical analysis. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        return ContentBegin + CopiedCharN;
    }

    QUEX_INLINE uint8_t*
    QUEX_FUNC(buffer_fill_region_append_conversion)(QUEX_TYPE_ANALYZER*  me,
                                                    uint8_t*             ContentBegin, 
                                                    uint8_t*             ContentEnd)
    /* Appends the content first into a 'raw' buffer and then converts it. This
     * is useful in cases where the 'break' may appear in between characters, or
     * where the statefulness of the converter cannot be controlled.              */
    {
        /* The buffer filler for direct memory handling must be of a 'void' specialization. */
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = \
                  (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);

        /* (1) Append the content to the 'raw' buffer. */
        /*     -- Move away passed buffer content.                                      */
        QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(filler);

        const size_t CopiedByteN = QUEX_NAME(MemoryManager_insert)(filler->raw_buffer.end, 
                                                        filler->raw_buffer.memory_end,
                                                        (uint8_t*)ContentBegin, 
                                                        (uint8_t*)ContentEnd);

        filler->raw_buffer.end += CopiedByteN;

        /* (2) Convert data from the 'raw' buffer into the analyzer buffer.             */

        /*     -- Move away passed buffer content.                                      */
        QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p = me->buffer._memory._end_of_file_p;
        filler->converter->convert(filler->converter, 
                                   &filler->raw_buffer.iterator, filler->raw_buffer.end,
                                   &insertion_p,                 QUEX_NAME(Buffer_content_back)(&me->buffer) + 1);

        if( me->buffer._byte_order_reversion_active_f ) 
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(me->buffer._memory._end_of_file_p, insertion_p);

        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, insertion_p);

        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        return ContentBegin + CopiedByteN;
    }

    QUEX_INLINE uint8_t*
    QUEX_FUNC(buffer_fill_region_append_conversion_direct)(QUEX_TYPE_ANALYZER*  me,
                                                              uint8_t*             ContentBegin, 
                                                              uint8_t*             ContentEnd)
    /* Does the conversion directly from the given user buffer to the internal 
     * analyzer buffer. Note, that this can only be used, if it is safe to assume
     * that appended chunks do not break in between the encoding of a single 
     * character.                                                                  */
    {
        /* The buffer filler for direct memory handling must be of a 'void' specialization. */
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;
        __quex_assert(ContentEnd > ContentBegin);
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);

        /*     -- Move away passed buffer content.                                      */
        QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p   = me->buffer._memory._end_of_file_p;
        uint8_t*              content_begin = ContentBegin;
        filler->converter->convert(filler->converter, 
                                   &content_begin, ContentEnd,
                                   &insertion_p,  QUEX_NAME(Buffer_content_back)(&me->buffer) + 1);

        if( me->buffer._byte_order_reversion_active_f ) 
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(me->buffer._memory._end_of_file_p, insertion_p);

        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, insertion_p);

        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
        /* 'content_begin' has been adapted by the converter. */
        return content_begin;
    }

    QUEX_INLINE void
    QUEX_FUNC(buffer_fill_region_prepare)(QUEX_TYPE_ANALYZER* me)
    {
        /* Move away unused passed buffer content. */
        QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_FUNC(buffer_fill_region_begin)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_NAME(Buffer_text_end)(&me->buffer); 
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_FUNC(buffer_fill_region_end)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_NAME(Buffer_content_back)(&me->buffer) + 1; 
    }

    QUEX_INLINE size_t
    QUEX_FUNC(buffer_fill_region_size)(QUEX_TYPE_ANALYZER* me)
    { 
        return   QUEX_FUNC(buffer_fill_region_end)(me) \
               - QUEX_FUNC(buffer_fill_region_begin)(me); 
    }

    QUEX_INLINE void
    QUEX_FUNC(buffer_fill_region_finish)(QUEX_TYPE_ANALYZER*  me,
                                         const size_t         CharacterN)
    {
        __quex_assert(me->buffer._memory._end_of_file_p + CharacterN <= me->buffer._memory._back);

        /* We assume that the content from '_end_of_file_p' to '_end_of_file_p + CharacterN'
         * has been filled with data.                                                        */
        if( me->buffer._byte_order_reversion_active_f ) 
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, 
                                        me->buffer._memory._end_of_file_p + CharacterN);

        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(me->buffer._memory._end_of_file_p, 
                                                me->buffer._memory._end_of_file_p + CharacterN);

        /* When lexing directly on the buffer, the end of file pointer is always set.        */
        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, 
                                   me->buffer._memory._end_of_file_p + CharacterN); 
    }

    QUEX_INLINE void
    QUEX_FUNC(buffer_conversion_fill_region_prepare)(QUEX_TYPE_ANALYZER* me) 
    {
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;

        /* It is always assumed that the buffer filler w/ direct buffer accesss
         * is a converter. Now, move away past content in the raw buffer.       */
        QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(filler);
    }

    QUEX_INLINE uint8_t*  
    QUEX_FUNC(buffer_conversion_fill_region_begin)(QUEX_TYPE_ANALYZER* me)
    { 
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;
        return filler->raw_buffer.end;
    }
    
    QUEX_INLINE uint8_t*  
    QUEX_FUNC(buffer_conversion_fill_region_end)(QUEX_TYPE_ANALYZER* me)
    { 
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;

        return filler->raw_buffer.memory_end;
    }
    
    QUEX_INLINE size_t
    QUEX_FUNC(buffer_conversion_fill_region_size)(QUEX_TYPE_ANALYZER* me)
    { 
        return   QUEX_FUNC(buffer_conversion_fill_region_end)(me) \
               - QUEX_FUNC(buffer_conversion_fill_region_begin)(me); 
    }

    QUEX_INLINE void
    QUEX_FUNC(buffer_conversion_fill_region_finish)(QUEX_TYPE_ANALYZER* me,
                                                       const size_t        ByteN)
    {
        QUEX_NAME(BufferFiller_Converter)<void>*  filler = (QUEX_NAME(BufferFiller_Converter)<void>*)me->buffer.filler;

        filler->raw_buffer.end += ByteN;

        /*     -- Move away passed buffer content.                                      */
        QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);

        /*     -- Perform the conversion.                                               */
        QUEX_TYPE_CHARACTER*  insertion_p = me->buffer._memory._end_of_file_p;
        filler->converter->convert(filler->converter, 
                                   &filler->raw_buffer.iterator, filler->raw_buffer.end,
                                   &insertion_p,                 QUEX_NAME(Buffer_content_back)(&me->buffer) + 1);

        if( me->buffer._byte_order_reversion_active_f ) 
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, insertion_p);

        /*      -- 'convert' has adapted the insertion_p so that is points to the first 
         *         position after the last filled position.                             */
        /*      -- double check that no buffer limit code is mixed under normal content */
        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(me->buffer._memory._end_of_file_p, insertion_p);

        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, insertion_p);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_FUNC(buffer_lexeme_start_pointer_get)(QUEX_TYPE_ANALYZER* me) 
    { return me->buffer._lexeme_start_p; }

    QUEX_INLINE void
    QUEX_FUNC(buffer_input_pointer_set)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* Adr)
    { me->buffer._input_p = Adr; }

#   ifndef __QUEX_SETTING_PLAIN_C
    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_MEMBER(buffer_fill_region_append)(QUEX_TYPE_CHARACTER*  ContentBegin, QUEX_TYPE_CHARACTER*  ContentEnd)
    { return QUEX_FUNC(buffer_fill_region_append)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE uint8_t*
    QUEX_MEMBER(buffer_fill_region_append_conversion)(uint8_t*  ContentBegin, uint8_t*  ContentEnd)
    { return QUEX_FUNC(buffer_fill_region_append_conversion)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE uint8_t*
    QUEX_MEMBER(buffer_fill_region_append_conversion_direct)(uint8_t*  ContentBegin, uint8_t*  ContentEnd)
    { return QUEX_FUNC(buffer_fill_region_append_conversion_direct)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_fill_region_prepare)()
    { QUEX_FUNC(buffer_fill_region_prepare)(this); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_fill_region_begin)()
    { return QUEX_FUNC(buffer_fill_region_begin)(this); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_fill_region_end)()
    { return QUEX_FUNC(buffer_fill_region_end)(this); }

    QUEX_INLINE size_t
    QUEX_MEMBER(buffer_fill_region_size)()
    { return QUEX_FUNC(buffer_fill_region_size)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_fill_region_finish)(const size_t CharacterN)
    { QUEX_FUNC(buffer_fill_region_finish)(this, CharacterN); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_conversion_fill_region_prepare)() 
    { QUEX_FUNC(buffer_fill_region_prepare)(this); }

    QUEX_INLINE uint8_t*  
    QUEX_MEMBER(buffer_conversion_fill_region_begin)()
    { return QUEX_FUNC(buffer_conversion_fill_region_begin)(this); }
    
    QUEX_INLINE uint8_t*  
    QUEX_MEMBER(buffer_conversion_fill_region_end)()
    { return QUEX_FUNC(buffer_conversion_fill_region_end)(this); }
    
    QUEX_INLINE size_t
    QUEX_MEMBER(buffer_conversion_fill_region_size)()
    { return QUEX_FUNC(buffer_conversion_fill_region_size)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_conversion_fill_region_finish)(const size_t ByteN)
    { QUEX_FUNC(buffer_conversion_fill_region_finish)(this, ByteN); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_lexeme_start_pointer_get)() 
    { return QUEX_FUNC(buffer_lexeme_start_pointer_get)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_input_pointer_set)(QUEX_TYPE_CHARACTER* Adr)
    { QUEX_FUNC(buffer_input_pointer_set)(this, Adr); }
#   endif

QUEX_NAMESPACE_MAIN_CLOSE


