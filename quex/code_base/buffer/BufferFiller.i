/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/Buffer_debug>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void       QUEX_NAME(__BufferFiller_on_overflow)(QUEX_NAME(Buffer)*, bool ForwardF);
                           
    QUEX_INLINE QUEX_TYPE_STREAM_POSITION     
                           QUEX_NAME(__BufferFiller_read_characters)(QUEX_NAME(BufferFiller)*, 
                                                                     QUEX_TYPE_CHARACTER*, 
                                                                     const ptrdiff_t,
                                                                     ptrdiff_t*);

    QUEX_INLINE void*      QUEX_NAME(BufferFiller_fill)(QUEX_NAME(Buffer)* buffer, 
                                                        const void*        ContentBegin, 
                                                        const void*        ContentEnd);
    QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_prepare)(QUEX_NAME(Buffer)*  buffer, 
                                                                void**              begin_p, 
                                                                const void**        end_p);
    QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_finish)(QUEX_NAME(Buffer)* buffer,
                                                               const void*        FilledEndP);

    QUEX_INLINE QUEX_NAME(BufferFiller)*
    QUEX_NAME(BufferFiller_new)(ByteLoader*           byte_loader, 
                                QUEX_NAME(Converter)* converter,
                                const char*           CharacterEncodingName,
                                const size_t          TranslationBufferMemorySize)
        /* CharacterEncoding == 0x0: Impossible; Converter requires codec name --> filler = 0x0
         * input_handle      == 0x0: Possible; Converter might be applied on buffer. 
         *                           (User writes into translation buffer).                     */
    {
        QUEX_NAME(BufferFiller)* filler;
        (void)TranslationBufferMemorySize;

#       if    defined(QUEX_OPTION_CONVERTER_ICONV) \
           || defined(QUEX_OPTION_CONVERTER_ICU) 
        if( ! CharacterEncodingName ) {
#           ifndef QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED
            __QUEX_STD_printf("Warning: No character encoding name specified, while this\n" \
                              "Warning: analyzer was generated for use with a converter.\n" \
                              "Warning: Please, consult the documentation about the constructor\n" \
                              "Warning: or the reset function. If it is desired to do a plain\n" \
                              "Warning: buffer filler with this setup, you might want to disable\n" \
                              "Warning: this warning with the macro:\n" \
                              "Warning:     QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED\n");
#           endif
            return (QUEX_NAME(BufferFiller*))0x0;
        } 
#       endif

        /* byte_loader = 0; possible if memory is filled manually. */

        if( converter ) {
            filler = QUEX_NAME(BufferFiller_Converter_new)(byte_loader,
                                                           converter, CharacterEncodingName, 
                                                           /* Internal Coding: Default */0x0,
                                                           TranslationBufferMemorySize);
        }
        else {
            filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader); 
        }
        
        return filler;
    }

    QUEX_INLINE QUEX_NAME(BufferFiller)* 
    QUEX_NAME(BufferFiller_DEFAULT)(ByteLoader*   byte_loader, 
                                    const char*   CharacterEncodingName) 
    {
#       if   defined(QUEX_OPTION_CONVERTER_ICU)
        QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_ICU_new)();
#       elif defined(QUEX_OPTION_CONVERTER_ICONV)
        QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_IConv_new)();
#       else
        QUEX_NAME(Converter)* converter = (QUEX_NAME(Converter)*)0;
#       endif
        if( converter ) {
            converter->ownership = E_Ownership_LEXICAL_ANALYZER;
        }
        return QUEX_NAME(BufferFiller_new)(byte_loader, converter,
                                           CharacterEncodingName, 
                                           QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
    }

    QUEX_INLINE void       
    QUEX_NAME(BufferFiller_delete)(QUEX_NAME(BufferFiller)** me)
    { 
        if     ( ! *me )                                           return;
        else if( (*me)->ownership != E_Ownership_LEXICAL_ANALYZER) return;
        else if( (*me)->delete_self )                              (*me)->delete_self(*me);
        (*me) = (QUEX_NAME(BufferFiller)*)0;
    }

    QUEX_INLINE void    
    QUEX_NAME(BufferFiller_setup)(QUEX_NAME(BufferFiller)*   me,
                                  QUEX_TYPE_STREAM_POSITION    
                                               (*tell_character_index)(QUEX_NAME(BufferFiller)*),
                                  void         (*seek_character_index)(QUEX_NAME(BufferFiller)*, 
                                                                       const QUEX_TYPE_STREAM_POSITION),
                                  size_t       (*read_characters)(QUEX_NAME(BufferFiller)*,
                                                                  QUEX_TYPE_CHARACTER*, const size_t),
                                  void         (*delete_self)(QUEX_NAME(BufferFiller)*),
                                  void         (*derived_fill_prepare)(QUEX_NAME(Buffer)*  me,
                                                                       void**              begin_p,
                                                                       const void**        end_p),
                                  ptrdiff_t    (*derived_fill_finish)(QUEX_NAME(BufferFiller)*   me,
                                                                      QUEX_TYPE_CHARACTER*       BeginP,
                                                                      const QUEX_TYPE_CHARACTER* EndP,
                                                                      const void*                FilledEndP),
                                  ByteLoader*  byte_loader)
    {
        __quex_assert(me);
        __quex_assert(tell_character_index);
        __quex_assert(seek_character_index);
        __quex_assert(read_characters);
        __quex_assert(delete_self);

        /* Support for buffer filling without user interaction               */
        me->tell_character_index = tell_character_index;
        me->seek_character_index = seek_character_index;
        me->read_characters      = read_characters;
        me->delete_self          = delete_self;
        me->_on_overflow         = 0x0;

        /* Support for manual buffer filling.                                */
        me->fill                 = QUEX_NAME(BufferFiller_fill);

        me->fill_prepare         = QUEX_NAME(BufferFiller_fill_prepare);
        me->fill_finish          = QUEX_NAME(BufferFiller_fill_finish);
        me->derived_fill_prepare = derived_fill_prepare;
        me->derived_fill_finish  = derived_fill_finish;

        me->byte_loader          = byte_loader;

        me->_byte_order_reversion_active_f = false;

        /* Default: External ownership */
        me->ownership = E_Ownership_EXTERNAL;
    }

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_reset)(QUEX_NAME(BufferFiller)* me, ByteLoader* new_byte_loader)
    {
        __quex_assert(new_byte_loader);

        if( new_byte_loader == me->byte_loader ) {
            /* nothing to be done. */
        }
        else if( ByteLoader_compare(new_byte_loader, me->byte_loader) ) {
            QUEX_ERROR_EXIT("Upon 'reset': current and new ByteLoader objects contain same input handle.");
        }
        else {
            ByteLoader_delete(&me->byte_loader);
            me->byte_loader = new_byte_loader;
        }

        me->byte_loader->seek(me->byte_loader, (QUEX_TYPE_STREAM_POSITION)0);
    }

    QUEX_INLINE size_t
    QUEX_NAME(BufferFiller_load_forward)(QUEX_NAME(Buffer)* buffer)
    /* Load new content into the buffer so that the analyzer can continue 
     * seeminglessly. 
     *
     * RETURNS: '>= 0'   distance that was moved forward. NOT the number 
     *                   of loaded characters.
     *          '-1'     if forward loading was not possible (end of file)                      
     *
     * NOTE:                                                              
     * There is a seemingly dangerous case where the loading **just**
     * fills the buffer to the limit. In this case no 'End Of File' is
     * detected, no end of file pointer is set, and as a consequence a new
     * loading will happen later. This new loading, though, will only copy
     * the fallback-region. The 'LoadedN == 0' will cause the
     * input.end_p to be set to the end of the copied
     * fallback-region. And everything is fine.                              */
    {
        QUEX_TYPE_CHARACTER*      BackP       = buffer->_memory._back;
        const ptrdiff_t           ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
        ptrdiff_t                 loaded_n;
        ptrdiff_t                 move_distance;
        QUEX_TYPE_STREAM_POSITION end_character_index;
        QUEX_TYPE_CHARACTER*      end_p;
        QUEX_NAME(BufferFiller)*  me;

        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        __quex_debug_buffer_load(buffer, "FORWARD(entry)\n");

        me = buffer->filler;
        if( ! me ) return 0; /* Possible, if no filler specified             */

        /* DETECT OVERFLOW: If stretch from _read_p to _lexeme_start_p spans 
         * the whole buffer, then nothing can be loaded into it.             */
        if( buffer->_read_p - buffer->_lexeme_start_p >= ContentSize ) { 
            QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ true);
            return 0;
        }

        /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
         * -- _read_p = Beginning of the Buffer: Reload nonsense. Maximum 
         *    size of available content lies ahead of '_read_p'.
         * -- input.end_p != 0: Tail of file read is already in buffer. */
        if     ( buffer->_read_p <= buffer->_memory._front ) return 0; 
        else if( buffer->input.end_p )             return 0; 

        /* Move old content that has to remain (fall back region)            */
        move_distance = QUEX_NAME(Buffer_move_away_passed_content)(buffer);
        if( ! move_distance ) return 0; 

        /* Load new content                                                  
         *
         * Due to backward loading the character index might not stand on the
         * end of the buffer. Thus a seek is necessary.                      */
        me->seek_character_index(me, buffer->input.end_character_index);

        end_character_index = \
                  QUEX_NAME(__BufferFiller_read_characters)(buffer->filler, 
                                                            buffer->_read_p, 
                                                            move_distance, 
                                                            &loaded_n);
        end_p               = (loaded_n == move_distance) ? (QUEX_TYPE_CHARACTER*)0
                                                          : &BackP[move_distance - loaded_n];
        QUEX_NAME(Buffer_input_end_set)(buffer, end_p, end_character_index);
        
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        /* Upon state entry, _read_p is incremented, thus decrement here    
         * => Next '*_read_p' reads first new content.                      */
        buffer->_read_p -= 1;      

        __quex_debug_buffer_load(buffer, "LOAD FORWARD(exit)\n");
        /* Return value is used for adaptions of memory addresses. The address
         * offset != loaded_n; => Return move_distance!                      */
        return (size_t)move_distance; 
    }

    QUEX_INLINE size_t   
    QUEX_NAME(BufferFiller_load_backward)(QUEX_NAME(Buffer)* buffer)
    /* Load *previous* content into the buffer so that the analyzer can 
     * continue seeminglessly (in backward direction).
     *
     * RETURNS: '>= 0'   distance that was moved backward. NOT the number 
     *                   of loaded characters.
     *          '-1'     if forward loading was not possible (end of file)   */
    {
        QUEX_NAME(BufferFiller)*   me = buffer->filler;
        QUEX_TYPE_CHARACTER*       ContentFront  = QUEX_NAME(Buffer_content_front)(buffer);
        QUEX_TYPE_CHARACTER*       ContentBack   = QUEX_NAME(Buffer_content_back)(buffer);
        ptrdiff_t                  move_distance = (ptrdiff_t)-1;

#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM_IN_BACKWARD_LOAD);
#       endif
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        if( ! me ) return 0; /* Possible, if no filler has been specified    */

        __quex_debug_buffer_load(buffer, "BACKWARD(entry)\n");

        /* DETECT OVERFLOW: If _lexeme_start_p is at back, then no new content
         * can be loaded.                                                    */
        if( buffer->_lexeme_start_p == ContentBack ) { 
            QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ false);
            return 0;
        }

        /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
         * -- _read_p = End of the Buffer: Reload nonsense. Maximum size of
         *    available content lies before of '_read_p' for backward lexing..
         * -- input.end_character_index == 0: Stading at begin, already.  */
        if     ( buffer->_read_p == buffer->_memory._back )            return 0;
        else if( QUEX_NAME(Buffer_character_index_begin)(buffer) == 0 ) return 0;

        /* Move old content that has to remain. The analyzer soon will have to 
         * go forward again, so some content better remains.                 */
        move_distance = QUEX_NAME(Buffer_move_away_upfront_content)(buffer); 

        /* Load new content                                                  
         *
         * It is not safe to assume that the character size is fixed. Thus it
         * is up to  the input strategy to determine the input position that
         * belongs to a character  position.                                 */
        me->seek_character_index(me,
                                 QUEX_NAME(Buffer_character_index_begin)(buffer)
                                 - move_distance);
        
        (void)QUEX_NAME(__BufferFiller_read_characters)(buffer->filler, 
                                                        ContentFront, 
                                                        move_distance, 
                                                        (ptrdiff_t*)0);
        /* input.end_character_index <-- Buffer_move_away_upfront_content */ 

        /* Upon state entry for backward lexing: _read_p is decremented, thus
         * increment here. => Next '*_read_p' reads first new content.      */
        buffer->_read_p += 1;

        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        __quex_debug_buffer_load(buffer, "BACKWARD(exit)\n");
        return (size_t)move_distance;
    }

    QUEX_INLINE void*
    QUEX_NAME(BufferFiller_fill)(QUEX_NAME(Buffer)*  buffer, 
                                 const void*         ContentBegin,
                                 const void*         ContentEnd)
    {
        ptrdiff_t      copy_n;
        void*          begin_p;
        const void*    end_p;

        /* Prepare the buffer for the reception of new input an acquire the
         * border pointers of where new content can be filled.               */
        buffer->filler->fill_prepare(buffer, &begin_p, &end_p);

        /* Copy as much as possible of the new content into the designated
         * region in memory.                                                 */
        copy_n = (ptrdiff_t)QUEXED(MemoryManager_insert)((uint8_t*)begin_p,  
                                                         (uint8_t*)end_p,
                                                         (uint8_t*)ContentBegin, 
                                                         (uint8_t*)ContentEnd);

        /* Flush into buffer what has been filled from &begin[0] to 
         * &begin[inserted_byte_n].                                          */
        buffer->filler->fill_finish(buffer, &((uint8_t*)begin_p)[copy_n]);

        /* Report a pointer to the first content element that has not yet 
         * been treated (== ContentEnd if all complete).                     */
        return (void*)&((uint8_t*)ContentBegin)[copy_n];
    }

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_fill_prepare)(QUEX_NAME(Buffer)*  buffer, 
                                         void**              begin_p, 
                                         const void**        end_p)
    /* RETURNS: The position of the first character that could not be copied
     *          into the fill region, because it did not have enough space.
     *          If the whole content was copied, then the return value
     *          is equal to BufferEnd.                                       */
    {
        (void)QUEX_NAME(Buffer_move_away_passed_content)(buffer);

        /* Get the pointers for the border where to fill content.           */
        buffer->filler->derived_fill_prepare(buffer, begin_p, end_p);

        __quex_assert(*end_p >= *begin_p);
    }

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_fill_finish)(QUEX_NAME(Buffer)* buffer,
                                        const void*        FilledEndP)
    {
        ptrdiff_t  inserted_character_n;

        /* Place new content in the engine's buffer.                         */
        inserted_character_n = buffer->filler->derived_fill_finish(buffer->filler, 
                                                                   QUEX_NAME(Buffer_text_end)(buffer),
                                                                   &QUEX_NAME(Buffer_content_back)(buffer)[1], 
                                                                   FilledEndP);

        /* Assume: content from 'input.end_p' to 'input.end_p[CharN]'
         * has been filled with data.                                        */
        if( buffer->filler->_byte_order_reversion_active_f ) {
            QUEX_NAME(Buffer_reverse_byte_order)(buffer->input.end_p, 
                                                 &buffer->input.end_p[inserted_character_n]);
        }

        /* When lexing directly on the buffer, the end of file pointer is 
         * always set.                                                       */
        QUEX_NAME(Buffer_input_end_set)(buffer, 
                                        &buffer->input.end_p[inserted_character_n],
                                        buffer->input.end_character_index + inserted_character_n);

        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    }

    QUEX_INLINE QUEX_TYPE_STREAM_POSITION       
    QUEX_NAME(__BufferFiller_read_characters)(QUEX_NAME(BufferFiller)* me, 
                                              QUEX_TYPE_CHARACTER*     memory, 
                                              const ptrdiff_t          CharacterNToRead,
                                              ptrdiff_t*               result_loaded_n)
    /* ADAPTS:  *loaded_n   number of actually loaded characters.
     * RETURNS: character index at end of loaded content.                    */
    {
        QUEX_TYPE_STREAM_POSITION  character_index_before = me->tell_character_index(me);
        QUEX_TYPE_STREAM_POSITION  character_index_after;
        ptrdiff_t                  loaded_n;
        
        loaded_n = me->read_characters(me, memory, (size_t)CharacterNToRead);

        character_index_after = me->tell_character_index(me);

        if(    character_index_after - character_index_before 
            != (QUEX_TYPE_STREAM_POSITION)loaded_n ) 
        {
            QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM); 
        }

        if( me->_byte_order_reversion_active_f ) {
            QUEX_NAME(Buffer_reverse_byte_order)(memory, &memory[loaded_n]);
        }
        if( result_loaded_n ) *result_loaded_n = loaded_n;
        return character_index_after;
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

