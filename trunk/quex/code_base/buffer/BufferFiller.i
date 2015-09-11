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
                           
    QUEX_INLINE size_t     QUEX_NAME(__BufferFiller_read_characters)(QUEX_NAME(Buffer)*, 
                                                                     QUEX_TYPE_CHARACTER*, 
                                                                     const ptrdiff_t);

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
    QUEX_NAME(BufferFiller_initial_load)(QUEX_NAME(Buffer)* buffer)
    {
        QUEX_NAME(BufferFiller)*  me           = buffer->filler;
        const ptrdiff_t           ContentSize  = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
        QUEX_TYPE_CHARACTER*      ContentFront = QUEX_NAME(Buffer_content_front)(buffer);
        ptrdiff_t                 loaded_n;

        /* Assume: Buffer initialization happens independently               */
        __quex_assert(buffer->_input_p        == ContentFront);   
        __quex_assert(buffer->_lexeme_start_p == ContentFront);

        /* end   != 0, means that the buffer is filled.
         * begin == 0, means that we are standing at the begin.
         * => end != 0 and begin == 0, initial content is loaded already.    */
        me->seek_character_index(me, 0);

        loaded_n = (ptrdiff_t)QUEX_NAME(__BufferFiller_read_characters)(buffer, ContentFront, ContentSize);

        buffer->_memory._end_of_file_p = (loaded_n != ContentSize) ? 
           &ContentFront[loaded_n]  /* end of file lies inside loaded region */
         : (QUEX_TYPE_CHARACTER*)0; /* end of file lies beyond               */


        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);
    } 

    QUEX_INLINE size_t
    QUEX_NAME(BufferFiller_load_forward)(QUEX_NAME(Buffer)* buffer)
    /*_________________________________________________________________________
     * This function is to be called as a reaction to a buffer limit code 'BLC'
     * as returned by 'get_forward()'. Its task is to load new content into the
     * buffer such that 'get_forward() can continue iterating. This means that
     * the '_input_p' points to one of the following positions:
     *
     *  (1) Beginning of the Buffer: In this case, no reload needs to take place.
     *      It can basically only appear if 'load_forward()' is called after
     *      'get_backward()'---and this does not make sense. But returning a '0'
     *      (which is >= 0 and indicates that everything is ok) tells the application 
     *      that nothing has been loaded, and the next 'get_forward()' will work 
     *      normally.
     *
     *  (2) End of File Pointer: (which may be equal to the end of the buffer) 
     *      In this case no further content can be loaded. The function returns '0'.
     *
     *  (3) End of Buffer (if it is != End of File Pointer): Here a 'normal' load of
     *      new data into the buffer can happen.
     *
     * RETURNS: '>= 0'   number of characters that were loaded forward in the stream.
     *          '-1'     if forward loading was not possible (end of file)                      
     *_________________________________________________________________________
     *
     * There is a seemingly dangerous case where the loading **just**
     * fills the buffer to the limit. In this case no 'End Of File' is
     * detected, no end of file pointer is set, and as a consequence a new
     * loading will happen later. This new loading, though, will only copy
     * the fallback-region. The 'LoadedN == 0' will cause the
     * _memory._end_of_file_p to be set to the end of the copied
     * fallback-region. And everything is fine.                          
     *_______________________________________________________________________*/
    {
        const ptrdiff_t           ContentSize  = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
        ptrdiff_t                 desired_load_n;
        size_t                    loaded_n = (size_t)-1;
        ptrdiff_t                 move_distance;
        QUEX_NAME(BufferFiller)*  me;

        __quex_assert(buffer);
        me = buffer->filler;
        if( ! me ) return 0; /* Possible, if no filler specified             */

        __quex_assert(me->tell_character_index);
        __quex_assert(me->seek_character_index);
        __quex_assert(me->read_characters);

        /* Catch impossible scenario: If the stretch from _input_p to
         * _lexeme_start_p spans the whole buffer content, then nothing can be
         * loaded into it.                                                   */
        if( buffer->_input_p - buffer->_lexeme_start_p >= ContentSize ) { 
            QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ true);
            return 0;
        }
        __quex_debug_buffer_load(buffer, "FORWARD(entry)\n");

        /* (*) Check for the three possibilities mentioned above */
        if     ( buffer->_input_p == buffer->_memory._front )         { return 0; }   /* (1)*/
        else if( buffer->_input_p == buffer->_memory._end_of_file_p ) { return 0; }   /* (2)*/
        else if( buffer->_input_p != buffer->_memory._back  ) {                     
            QUEX_ERROR_EXIT("Call to 'load_forward() but '_input_p' not on buffer border.\n" 
                            "(Check character encoding)");  
        }
        else if( buffer->_memory._end_of_file_p ) { 
            /* End of file has been reached before, we cannot load more.     */
            return 0;                               
        }
        /* HERE: _input_p ---> LAST ELEMENT OF THE BUFFER!              * (3)*/  

        /*___________________________________________________________________
         * (1) Handle fallback region                                        */
        move_distance = QUEX_NAME(Buffer_move_away_passed_content)(buffer);
        if( ! move_distance ) {
            return 0;
        }
        desired_load_n = buffer->_memory._back - buffer->_input_p;
        __quex_assert(move_distance == desired_load_n);

        /*___________________________________________________________________*/
        /* (2) Load new content
         *
         * NOTE: Due to backward loading the character index might not stand 
         *       on the end of the buffer. Thus a seek is necessary.         */
        me->seek_character_index(me, buffer->_content_character_index_end);

        loaded_n = QUEX_NAME(__BufferFiller_read_characters)(buffer, 
                                                             buffer->_input_p, 
                                                             desired_load_n);
        
        /*___________________________________________________________________*/
        /* (3) Adapt the pointers in the buffer*/
        buffer->_input_p -= 1;      /* Incremented upon state entry ...      */
        (void)loaded_n;             /* avoid 'loaded_n' not used w/o asserts */
        __quex_assert(   ! buffer->_memory._end_of_file_p 
                      || ((ptrdiff_t)loaded_n + move_distance) 
                          == buffer->_memory._end_of_file_p - buffer->_memory._front - 1);

        __quex_debug_buffer_load(buffer, "LOAD FORWARD(exit)\n");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);
        /* NOTE: Return value is used for adaptions of memory addresses. It happens that the*/
        /*       address offset is equal to desired_load_n; see function __forward_adapt_pointers().*/
        return (size_t)desired_load_n; /* THUS NOT: loaded_n*/
    }

    QUEX_INLINE size_t   
    QUEX_NAME(BufferFiller_load_backward)(QUEX_NAME(Buffer)* buffer)
    {
        QUEX_NAME(BufferFiller)*   me = buffer->filler;
        QUEX_TYPE_CHARACTER*       ContentFront = QUEX_NAME(Buffer_content_front)(buffer);
        QUEX_TYPE_CHARACTER*       ContentBack  = QUEX_NAME(Buffer_content_back)(buffer);
        ptrdiff_t                  BackwardDistance              = (ptrdiff_t)-1;
        QUEX_TYPE_STREAM_POSITION  NewContentCharacterIndexBegin = (ptrdiff_t)-1;

#       ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM_IN_BACKWARD_LOAD);
#       endif
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        if( ! me ) return 0; /* Possible, if no filler has been specified    */

        /* PURPOSE: This function is to be called as a reaction to a buffer limit code 'BLC'
         *          as returned by 'get_backward()'. Its task is the same as the one of 
         *          'load_forward()'--only in opposite direction. Here only two cases need 
         *          to be distinguished. The current_p points to 
         *
         *          (1) End of Buffer or End of File pointer: No backward load needs to 
         *              happen. This can only occur if a 'get_forward()' was called right
         *              before.
         *
         *          (2) Begin of the buffer and the buffer is the 'start buffer':
         *              in this case no backward load can happen, because we are at the 
         *              beginning. The function returns 0.
         *
         *          (3) Begin of buffer and _begin_of_file_f is not set!: This is the case
         *              where this function, actually, has some work to do. It loads the
         *              buffer with 'earlier' content from the file.
         *
         *
         * RETURNS: Distance that was loaded backwards.
         *          -1 in case of backward loading is not possible (begin of file)
         *     
         * COMMENT: 
         *     
         * For normal cases the fallback region, i.e. the 'FALLBACK_N' buffer bytes 
         * allows to go a certain distance backwards immediately. If still the begin 
         * of the buffer is reached, then this is an indication that something is
         * 'off-the-norm'. Lexical analysis is not supposed to go longtimes
         * backwards. For such cases we step a long stretch backwards: A
         * THIRD of the buffer's size! 
         *
         * A meaningful fallback_n would be 64 Bytes. If the buffer's size
         * is for example 512 kB then the backwards_distance of A THIRD means 170
         * kB. This leaves a  safety region which is about 2730 times
         * greater than normal (64 Bytes). After all, lexical analysis means
         * to go **mainly forward** and not backwards.  */
        __quex_assert(buffer != 0x0);
        __quex_debug_buffer_load(buffer, "BACKWARD(entry)\n");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        /* (*) Check for the three possibilities mentioned above*/
        if     ( buffer->_input_p == buffer->_memory._back )          { return 0; } /* (1) */
        else if( buffer->_input_p == buffer->_memory._end_of_file_p ) { return 0; } /* (1) */
        else if( buffer->_input_p != buffer->_memory._front ) {
            QUEX_ERROR_EXIT("Call to 'load_backward() but '_input_p' not on buffer border.\n" 
                            "(Check character encoding)");  
        }
        else if( QUEX_NAME(Buffer_character_index_begin)(buffer) == 0 ) { return 0; }  /* (2) */
        /*                                                                     * (3) */
        /* HERE: current_p == FRONT OF THE BUFFER!   
         *_______________________________________________________________________________*/
        /* Catch impossible scenario: If the stretch from _input_p to _lexeme_start_p 
         * spans the whole buffer content, then nothing can be loaded into it.           */
        if( buffer->_lexeme_start_p == ContentBack ) { 
            QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* ForwardF */ false);
            return 0;
        }

        /*_______________________________________________________________________________
         * (1) Compute distance to go backwards */
        BackwardDistance = QUEX_NAME(Buffer_move_away_upfront_content)(buffer); 

        /*_______________________________________________________________________________
         * (2) Compute the stream position of the 'start to read'   
         *  
         * It is not safe to assume that the character size is fixed. Thus it is up to  
         * the input strategy to determine the input position that belongs to a character  
         * position.                                                                     */
        NewContentCharacterIndexBegin = QUEX_NAME(Buffer_character_index_begin)(buffer) - BackwardDistance;
        __quex_assert(BackwardDistance != 0); /* if "_index_begin != 0", then backward load must be. */
        me->seek_character_index(me, NewContentCharacterIndexBegin);
        
        /* -- If file content < buffer size, then the start position of the stream to which  
         *    the buffer refers is always 0 and no backward loading will ever happen.  
         * -- If the file content >= buffer size, then backward loading must always fill  
         *    the buffer. */
        (void)QUEX_NAME(__BufferFiller_read_characters)(buffer, ContentFront, BackwardDistance);

        /*________________________________________________________________________________
         * (4) Adapt pointers */
        buffer->_input_p += 1;

        __quex_debug_buffer_load(buffer, "BACKWARD(exit)\n");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);

        return (size_t)BackwardDistance;
    }

    QUEX_INLINE void
    QUEX_NAME(__BufferFiller_on_overflow)(QUEX_NAME(Buffer)* buffer, bool ForwardF)
    {
        QUEX_NAME(BufferFiller)* me = buffer->filler;
#       ifdef QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE
        uint8_t               utf8_encoded_str[512]; 
        char                  message[1024];
        const size_t          MessageSize = (size_t)1024;
        uint8_t*              WEnd        = 0x0;
        uint8_t*              witerator   = 0x0; 
        QUEX_TYPE_CHARACTER*        End         = 0x0; 
        const QUEX_TYPE_CHARACTER*  iterator    = 0x0; 
#       endif

        if(    me->_on_overflow == 0x0
            || me->_on_overflow(buffer, ForwardF) == false ) {

#           ifdef QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE
            /* Print out the lexeme start, so that the user has a hint. */
            WEnd        = utf8_encoded_str + 512 - 7;
            witerator   = utf8_encoded_str; 
            End         = buffer->_memory._back; 
            iterator    = buffer->_lexeme_start_p; 

            QUEX_CONVERTER_STRING(QUEX_SETTING_CHARACTER_CODEC, utf8)(&iterator, End, &witerator, WEnd);

            message[0] = '\0';
            /* No use of 'snprintf()' because not all systems seem to support it propperly. */
            __QUEX_STD_strncat(message, 
                               "Distance between lexeme start and current pointer exceeds buffer size.\n"
                               "(tried to load buffer",
                               MessageSize);
            __QUEX_STD_strncat(message, ForwardF ? "forward)" : "backward)",                   MessageSize);
            __QUEX_STD_strncat(message, "As a hint consider the beginning of the lexeme:\n[[", MessageSize);
            __QUEX_STD_strncat(message, (char*)utf8_encoded_str,                               MessageSize);
            __QUEX_STD_strncat(message, "]]\n",                                                MessageSize);

            QUEX_ERROR_EXIT(message);
#           else
            QUEX_ERROR_EXIT("Distance between lexeme start and current pointer exceeds buffer size.\n"
                            "(tried to load buffer forward). Please, compile with option\n\n"
                            "    QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE\n\n"
                            "in order to get a more informative output. Most likely, one of your patterns\n"
                            "eats longer as you inteded it. Alternatively you might want to set the buffer\n"
                            "size to a greate value or use skippers (<skip: [ \\n\\t]> for example).\n");
#           endif /* QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE */
        }
    }

    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_step_forward_n_characters)(QUEX_NAME(BufferFiller)* me,
                                                      const ptrdiff_t          ForwardN)
    { 
        /* STRATEGY: Starting from a certain point in the file we read characters
         *           Convert one-by-one until we reach the given character index. 
         *           This is, of course, incredibly inefficient but safe to work under
         *           all circumstances. Fillers should only rely on this function
         *           in case of no other alternative. Also, caching some information 
         *           about what character index is located at what position may help
         *           to increase speed.                                                */      
#       ifdef QUEX_OPTION_ASSERTS
        const QUEX_TYPE_STREAM_POSITION TargetIndex = me->tell_character_index(me) + (QUEX_TYPE_STREAM_POSITION)ForwardN;
#       endif

        /* START: We are now at character index 'CharacterIndex - remaining_character_n'.
         * LOOP:  It remains to interpret 'remaining_character_n' number of characters. Since 
         *        the interpretation is best done using a buffer, we do this in chunks.      */ 
        size_t               remaining_character_n = (size_t)ForwardN;
        const size_t         ChunkSize             = QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE;
        QUEX_TYPE_CHARACTER  chunk[QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE];

        __quex_assert(QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE >= 1);

        /* We CANNOT assume that end the end it will hold: 
         *
         *       __quex_assert(me->tell_character_index(me) == TargetIndex);
         *
         * Because, we do not know wether the stream actually has so many characters.     */
        for(; remaining_character_n > ChunkSize; remaining_character_n -= ChunkSize )  
            if( me->read_characters(me, (QUEX_TYPE_CHARACTER*)chunk, ChunkSize) < ChunkSize ) {
                __quex_assert(me->tell_character_index(me) <= TargetIndex);
                return;
            }
        if( remaining_character_n ) 
            me->read_characters(me, (QUEX_TYPE_CHARACTER*)chunk, remaining_character_n);
       
        __quex_assert(me->tell_character_index(me) <= TargetIndex);
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
        buffer->_content_character_index_end += inserted_character_n;

        /* Assume: content from '_end_of_file_p' to '_end_of_file_p[CharN]'
         * has been filled with data.                                        */
        if( buffer->filler->_byte_order_reversion_active_f ) {
            QUEX_NAME(Buffer_reverse_byte_order)(buffer->_memory._end_of_file_p, 
                                                 &buffer->_memory._end_of_file_p[inserted_character_n]);
        }

        QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(buffer->_memory._end_of_file_p, 
                                                &buffer->_memory._end_of_file_p[inserted_character_n]);
        /* When lexing directly on the buffer, the end of file pointer is 
         * always set.                                                       */
        QUEX_NAME(Buffer_end_of_file_set)(buffer, 
                                          &buffer->_memory._end_of_file_p[inserted_character_n]);

        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
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
    QUEX_NAME(__BufferFiller_read_characters)(QUEX_NAME(Buffer)*    buffer, 
                                              QUEX_TYPE_CHARACTER*  memory, 
                                              const ptrdiff_t       CharacterNToRead)
    {
        QUEX_TYPE_STREAM_POSITION  character_index_before_load = buffer->filler->tell_character_index(buffer->filler);
        size_t                     loaded_n;
        
        loaded_n  = buffer->filler->read_characters(buffer->filler, memory, 
                                                    (size_t)CharacterNToRead);

        buffer->_content_character_index_end = buffer->filler->tell_character_index(buffer->filler);

        if(    buffer->_content_character_index_end - character_index_before_load 
            != (QUEX_TYPE_STREAM_POSITION)loaded_n ) 
        {
            QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM); 
        }

        if( buffer->filler->_byte_order_reversion_active_f ) {
            QUEX_NAME(Buffer_reverse_byte_order)(memory, &memory[loaded_n]);
        }
        return loaded_n;
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

