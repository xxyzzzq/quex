/* -*- C++ -*- vim:set syntax=cpp:
 * (C) 2005-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY              */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I

#include <quex/code_base/definitions>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/buffer/Buffer>

#define QUEX_CAST_FILLER(FILLER) ((QUEX_NAME(BufferFiller_Converter)*)FILLER)

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE size_t 
    QUEX_NAME(BufferFillerUser_Plain_insert)(QUEX_NAME(BufferFiller)*  me,
                                             QUEX_TYPE_CHARACTER**     insertion_p,
                                             QUEX_TYPE_CHARACTER*      BufferEnd,
                                             void*                     ContentBegin,
                                             void*                     ContentEnd)
    {
        size_t InsertedByteN = 0;

        (void)me;

        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE((QUEX_TYPE_CHARACTER*)ContentBegin, 
                                                (QUEX_TYPE_CHARACTER*)ContentEnd);
        InsertedByteN = QUEXED(MemoryManager_insert)((uint8_t*)*insertion_p,  
                                                   (uint8_t*)BufferEnd,
                                                   (uint8_t*)ContentBegin, 
                                                   (uint8_t*)ContentEnd);

        *insertion_p += (InsertedByteN / sizeof(QUEX_TYPE_CHARACTER)); 

        return InsertedByteN;
    }


    QUEX_INLINE void*
    QUEX_NAME(buffer_fill_region_append_core)(QUEX_TYPE_ANALYZER*    me, 
                                              void*   ContentBegin, 
                                              void*   ContentEnd,
                                              size_t (*insert)(QUEX_NAME(BufferFiller)* me,
                                                               QUEX_TYPE_CHARACTER**    insertion_p,
                                                               QUEX_TYPE_CHARACTER*     BufferEnd,
                                                               void*                    ContentBegin,
                                                               void*                    ContentEnd))
    /* RETURNS: The position of the first character that could not be copied
     *          into the fill region, because it did not have enough space.
     *          If the whole content was copied, then the return value
     *          is equal to BufferEnd.                                        */
    {
        QUEX_TYPE_CHARACTER*  insertion_p          = 0x0;
        QUEX_TYPE_CHARACTER*  backup_p             = 0x0;
        QUEX_TYPE_CHARACTER*  insertion_end_p      = 0x0;
        size_t                inserted_byte_n      = 0;
        ptrdiff_t             inserted_character_n = 0;
        ptrdiff_t             moved_character_n    = 0;
        __quex_assert(ContentEnd > ContentBegin);

        /* (1) Move away unused passed buffer content. */
        moved_character_n = QUEX_NAME(buffer_fill_region_prepare)(me);

        /* (2) Determine place to insert new content */
        insertion_p     = QUEX_NAME(buffer_fill_region_begin)(me);
        backup_p        = insertion_p;
        insertion_end_p = QUEX_NAME(buffer_fill_region_end)(me);

        inserted_byte_n = insert(me->buffer.filler, 
                                 &insertion_p, insertion_end_p,
                                 ContentBegin, ContentEnd);

        inserted_character_n = insertion_p - backup_p;

        /* (3) Finish the writing. */
        me->buffer._content_character_index_begin += moved_character_n;
        me->buffer._content_character_index_end   += inserted_character_n;
        QUEX_NAME(buffer_fill_region_finish)(me, inserted_character_n);

        return &((uint8_t*)ContentBegin)[inserted_byte_n];
    }

    QUEX_INLINE void*
    QUEX_NAME(buffer_fill_region_append)(QUEX_TYPE_ANALYZER*    me, 
                                         void*                  ContentBegin, 
                                         void*                  ContentEnd)
    {
        __quex_assert(ContentEnd >= ContentBegin);

        return QUEX_NAME(buffer_fill_region_append_core)(me, 
                                                         ContentBegin, ContentEnd,
                                                         QUEX_NAME(BufferFillerUser_Plain_insert));
    }

    QUEX_INLINE ptrdiff_t
    QUEX_NAME(buffer_fill_region_prepare)(QUEX_TYPE_ANALYZER* me)
    {
        __quex_assert(me->buffer._memory._end_of_file_p != 0x0); 
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);

        /* Move away unused passed buffer content. */
        return QUEX_NAME(Buffer_move_away_passed_content)(&me->buffer);
    }

    QUEX_INLINE void
    QUEX_NAME(buffer_fill_region_finish)(QUEX_TYPE_ANALYZER*  me,
                                         const ptrdiff_t      CharacterN)
    {
        __quex_assert(me->buffer._memory._end_of_file_p); 
        __quex_assert(me->buffer._memory._end_of_file_p + CharacterN <= me->buffer._memory._back);

        /* We assume that the content from '_end_of_file_p' to '_end_of_file_p + CharacterN'
         * has been filled with data.                                                        */
        if( me->buffer._byte_order_reversion_active_f ) {
            QUEX_NAME(Buffer_reverse_byte_order)(me->buffer._memory._end_of_file_p, 
                                                 &me->buffer._memory._end_of_file_p[CharacterN]);
        }

        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(me->buffer._memory._end_of_file_p, 
                                                &me->buffer._memory._end_of_file_p[CharacterN]);

        /* When lexing directly on the buffer, the end of file pointer is always set.        */
        QUEX_NAME(Buffer_end_of_file_set)(&me->buffer, 
                                          &me->buffer._memory._end_of_file_p[CharacterN]);

        /* NOT:
         *      buffer->_input_p        = front;
         *      buffer->_lexeme_start_p = front;            
         * We might want to allow to append during lexical analysis. */
        QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_NAME(buffer_fill_region_begin)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_NAME(Buffer_text_end)(&me->buffer); 
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_NAME(buffer_fill_region_end)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_NAME(Buffer_content_back)(&me->buffer) + 1; 
    }

    QUEX_INLINE size_t
    QUEX_NAME(buffer_fill_region_size)(QUEX_TYPE_ANALYZER* me)
    { 
        ptrdiff_t delta =   QUEX_NAME(buffer_fill_region_end)(me) 
                          - QUEX_NAME(buffer_fill_region_begin)(me); 
        __quex_assert(delta >= 0);
        return (size_t)delta;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_NAME(buffer_lexeme_start_pointer_get)(QUEX_TYPE_ANALYZER* me) 
    { return me->buffer._lexeme_start_p; }

    QUEX_INLINE void
    QUEX_NAME(buffer_input_pointer_set)(QUEX_TYPE_ANALYZER* me, QUEX_TYPE_CHARACTER* Adr)
    { me->buffer._input_p = Adr; }


#   if defined(__QUEX_OPTION_CONVERTER)
    QUEX_INLINE size_t 
    QUEX_NAME(BufferFillerUser_Converter_insert)(QUEX_NAME(BufferFiller)* alter_ego,
                                                 QUEX_TYPE_CHARACTER**    buffer_insertion_p,
                                                 QUEX_TYPE_CHARACTER*     BufferEnd,
                                                 void*                    ContentBegin,
                                                 void*                    ContentEnd)
    /* Does the conversion directly from the given user buffer to the internal 
     * analyzer buffer. Note, that this can only be used, if it is safe to assume
     * that appended chunks do not break in between the encoding of a single 
     * character.                                                                  */
    {
        uint8_t*  content_p = (uint8_t*)ContentBegin;

        if( ContentBegin != ContentEnd ) {
            QUEX_CAST_FILLER(alter_ego)->converter->convert(QUEX_CAST_FILLER(alter_ego)->converter, 
                                                            &content_p, (uint8_t*)ContentEnd,
                                                            buffer_insertion_p, BufferEnd);
        }
        /* 'read_iterator' has been adapted by the converter, so that the 
         * number of read bytes can be determined by: read_iterator - ContentEnd */ 
        return (size_t)(content_p - (uint8_t*)ContentBegin);
    }

    QUEX_INLINE void 
    QUEX_NAME(buffer_fill_region_append_conversion)(QUEX_TYPE_ANALYZER*  me,
                                                    void*                ContentBegin, 
                                                    void*                ContentEnd)
    /* Appends the content first into a 'raw' buffer and then converts it. This
     * is useful in cases where the 'break' may appear in between characters, or
     * where the statefulness of the converter cannot be controlled.              */
    {
        size_t InsertedByteN = 0;
        __quex_assert(ContentEnd >= ContentBegin);

        QUEX_NAME(buffer_conversion_fill_region_prepare)(me);

        /* (1) Append the content to the 'raw' buffer. */
        /*     -- Move away passed buffer content.                                */
        InsertedByteN = QUEXED(MemoryManager_insert)(QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.end, 
                                                     QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.memory_end,
                                                     (uint8_t*)ContentBegin, 
                                                     (uint8_t*)ContentEnd);

        QUEX_NAME(buffer_conversion_fill_region_finish)(me, InsertedByteN);
    }

    QUEX_INLINE void*
    QUEX_NAME(buffer_fill_region_append_conversion_direct)(QUEX_TYPE_ANALYZER*  me,
                                                           void*                ContentBegin, 
                                                           void*                ContentEnd)
    /* Does the conversion directly from the given user buffer to the internal 
     * analyzer buffer. Note, that this can only be used, if it is safe to assume
     * that appended chunks do not break in between the encoding of a single 
     * character.                                                                  */
    {
        __quex_assert(ContentEnd >= ContentBegin);

        return QUEX_NAME(buffer_fill_region_append_core)(me, ContentBegin, ContentEnd,
                                                         QUEX_NAME(BufferFillerUser_Converter_insert));
    }

    QUEX_INLINE void
    QUEX_NAME(buffer_conversion_fill_region_prepare)(QUEX_TYPE_ANALYZER* me) 
    {
        /* If these asserts trigger, then the raw buffer has been initialized 
         * as 'empty'. That, is the constructor has not been asked to set it
         * up. Review the constructor call to the lexical analyzer!            */
        __quex_assert(QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.begin);
        __quex_assert(   QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.memory_end
                      != QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.begin);

        /* It is always assumed that the buffer filler w/ direct buffer accesss
         * is a converter. Now, move away past content in the raw buffer.       */
        QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(QUEX_CAST_FILLER(me->buffer.filler));
    }

    QUEX_INLINE void*
    QUEX_NAME(buffer_conversion_fill_region_finish)(QUEX_TYPE_ANALYZER* me,
                                                    const size_t        ByteN)
    {
        void* result;

        __quex_assert(  QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.memory_end
                      - QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.end >= (ptrdiff_t)ByteN);

        QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.end += ByteN;

        result = QUEX_NAME(buffer_fill_region_append_core)(me, 
                                                           QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.iterator, 
                                                           QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.end, 
                                                           QUEX_NAME(BufferFillerUser_Converter_insert));

        QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.iterator = (uint8_t*)result;

        return result;
    }

    QUEX_INLINE uint8_t*  
    QUEX_NAME(buffer_conversion_fill_region_begin)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.end;
    }
    
    QUEX_INLINE uint8_t*  
    QUEX_NAME(buffer_conversion_fill_region_end)(QUEX_TYPE_ANALYZER* me)
    { 
        return QUEX_CAST_FILLER(me->buffer.filler)->raw_buffer.memory_end;
    }
    
    QUEX_INLINE size_t
    QUEX_NAME(buffer_conversion_fill_region_size)(QUEX_TYPE_ANALYZER* me)
    { 
        ptrdiff_t delta =   QUEX_NAME(buffer_conversion_fill_region_end)(me) 
                          - QUEX_NAME(buffer_conversion_fill_region_begin)(me); 
        __quex_assert(delta >= 0);
        return (size_t)delta;
    }

#   endif

#   ifndef __QUEX_OPTION_PLAIN_C
    QUEX_INLINE void*
    QUEX_MEMBER(buffer_fill_region_append)(void*  ContentBegin, void*  ContentEnd)
    { return QUEX_NAME(buffer_fill_region_append)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE ptrdiff_t
    QUEX_MEMBER(buffer_fill_region_prepare)()
    { return QUEX_NAME(buffer_fill_region_prepare)(this); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_fill_region_begin)()
    { return QUEX_NAME(buffer_fill_region_begin)(this); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_fill_region_end)()
    { return QUEX_NAME(buffer_fill_region_end)(this); }

    QUEX_INLINE size_t
    QUEX_MEMBER(buffer_fill_region_size)()
    { return QUEX_NAME(buffer_fill_region_size)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_fill_region_finish)(const ptrdiff_t CharacterN)
    { QUEX_NAME(buffer_fill_region_finish)(this, CharacterN); }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_MEMBER(buffer_lexeme_start_pointer_get)() 
    { return QUEX_NAME(buffer_lexeme_start_pointer_get)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_input_pointer_set)(QUEX_TYPE_CHARACTER* Adr)
    { QUEX_NAME(buffer_input_pointer_set)(this, Adr); }

#   if defined(__QUEX_OPTION_CONVERTER)
    QUEX_INLINE void 
    QUEX_MEMBER(buffer_fill_region_append_conversion)(void*  ContentBegin, void*  ContentEnd)
    { QUEX_NAME(buffer_fill_region_append_conversion)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE void*
    QUEX_MEMBER(buffer_fill_region_append_conversion_direct)(void*  ContentBegin, void*  ContentEnd)
    { return QUEX_NAME(buffer_fill_region_append_conversion_direct)(this, ContentBegin, ContentEnd); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_conversion_fill_region_prepare)() 
    { QUEX_NAME(buffer_conversion_fill_region_prepare)(this); }

    QUEX_INLINE uint8_t*  
    QUEX_MEMBER(buffer_conversion_fill_region_begin)()
    { return QUEX_NAME(buffer_conversion_fill_region_begin)(this); }
    
    QUEX_INLINE uint8_t*  
    QUEX_MEMBER(buffer_conversion_fill_region_end)()
    { return QUEX_NAME(buffer_conversion_fill_region_end)(this); }
    
    QUEX_INLINE size_t
    QUEX_MEMBER(buffer_conversion_fill_region_size)()
    { return QUEX_NAME(buffer_conversion_fill_region_size)(this); }

    QUEX_INLINE void
    QUEX_MEMBER(buffer_conversion_fill_region_finish)(const size_t ByteN)
    { QUEX_NAME(buffer_conversion_fill_region_finish)(this, ByteN); }
#   endif

#   endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef QUEX_CAST_FILLER

#include <quex/code_base/buffer/Buffer.i>

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MEMBER__BUFFER_ACCESS_I */

