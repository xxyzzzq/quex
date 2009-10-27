/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/BufferFiller>

#include <quex/code_base/temporary_macros_on>

#if ! defined(__QUEX_SETTING_PLAIN_C)
#   include <stdexcept>
#endif
QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE size_t  __QuexBufferFiller_forward_compute_fallback_region(QuexBuffer*  buffer,
                                                                           const size_t Distance_LexemeStart_to_InputP);
    QUEX_INLINE void    __QuexBufferFiller_forward_copy_fallback_region(QuexBuffer*,
                                                                        const size_t FallBackN);
    QUEX_INLINE void    __QuexBufferFiller_forward_adapt_pointers(QuexBuffer*, 
                                                                  const size_t DesiredLoadN,
                                                                  const size_t LoadedN,
                                                                  const size_t FallBackN, 
                                                                  const size_t Distance_LexemeStart_to_InputP);
    QUEX_INLINE size_t  __QuexBufferFiller_backward_compute_backward_distance(QuexBuffer* buffer);
    QUEX_INLINE void    __QuexBufferFiller_backward_copy_backup_region(QuexBuffer*, 
                                                                       const size_t BackwardDistance);
    QUEX_INLINE void    __QuexBufferFiller_backward_adapt_pointers(QuexBuffer*, 
                                                                   const size_t BackwardDistance);
    QUEX_INLINE void    __QuexBufferFiller_on_overflow(QuexBuffer*, bool ForwardF);

    QUEX_INLINE size_t       
    __BufferFiller_read_characters(QuexBuffer*, QUEX_TYPE_CHARACTER*, const size_t);

    TEMPLATE_IN(InputHandleT) QuexBufferFiller*
    QuexBufferFiller_new(InputHandleT*  input_handle, 
                         const char*    CharacterEncodingName,
                         const size_t   TranslationBufferMemorySize)
    {
        if( CharacterEncodingName != 0x0 ) {

            if( QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW == 0x0 ) {
                QUEX_ERROR_EXIT("Use of buffer filler type 'CharacterEncodingName' while " \
                                "'QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW' has not\n" \
                                "been defined (use --iconv, --icu, --converter-new to specify converter).\n");
            }

            /* The specification of a CharacterEncodingName means that a converter is
             * to be used. This can also happen if the engine is to work on plain memory.
             * In the latter case the input_handle = 0x0 is passed to the 'new' allocator
             * without the slightest harm.                                                 */
            return (QuexBufferFiller*)QuexBufferFiller_Converter_new(input_handle, 
                                  QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW,
                                  CharacterEncodingName, /* Internal Coding: Default */0x0,
                                  TranslationBufferMemorySize);
       
        } else {
#           if defined(__QUEX_OPTION_CONVERTER_ENABLED) 
#           ifndef QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED
            __QUEX_STD_printf("Warning: No character encoding name specified, while this\n" \
                              "Warning: analyzer was generated for use with a converter.\n" \
                              "Warning: Please, consult the documentation about the constructor\n" \
                              "Warning: or the reset function. If is is desired to do a plain\n" \
                              "Warning: buffer filler with this setup, you might want to disable\n" \
                              "Warning: this warning with the macro:\n" \
                              "Warning:     QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED\n");
#           endif
#           endif
            /* If no converter is required, it has to be considered whether the buffer needs
             * filling or not. If the input source is not memory, then the 'plain' buffer
             * filling is applied. If the input source is memory, no filler is required.   */
            return (input_handle == 0x0) ? 0x0 : (QuexBufferFiller*)QuexBufferFiller_Plain_new(input_handle);
        }
    }

    QUEX_INLINE void       
    QuexBufferFiller_delete_self(QuexBufferFiller* me)
    { 
        /* if no dedicated deallocator is specified then free only the basic
         * BufferFiller structure.                                           */
        if( me->delete_self == 0x0 ) __QUEX_FREE_MEMORY(me);
        else                         me->delete_self(me);
    }

    QUEX_INLINE void
    __QuexBufferFiller_setup_functions(QuexBufferFiller* me,
                                       size_t       (*tell_character_index)(QuexBufferFiller*),
                                       void         (*seek_character_index)(QuexBufferFiller*, const size_t),
                                       size_t       (*read_characters)(QuexBufferFiller*,
                                                                       QUEX_TYPE_CHARACTER*, const size_t),
                                       void         (*delete_self)(QuexBufferFiller*))
    {
        __quex_assert(me != 0x0);
        __quex_assert(tell_character_index != 0x0);
        __quex_assert(seek_character_index != 0x0);
        __quex_assert(read_characters != 0x0);
        __quex_assert(delete_self != 0x0);


        me->tell_character_index = tell_character_index;
        me->seek_character_index = seek_character_index;
        me->read_characters      = read_characters;
        me->_on_overflow         = 0x0;
        me->delete_self          = delete_self;
    }

    QUEX_INLINE void
    QuexBufferFiller_initial_load(QuexBuffer* buffer)
    {
        const size_t         ContentSize  = QuexBuffer_content_size(buffer);
        QUEX_TYPE_CHARACTER* ContentFront = QuexBuffer_content_front(buffer);
        QuexBufferFiller*    me           = buffer->filler;

        /* Assume: Buffer initialization happens independently */
        __quex_assert(buffer->_input_p        == ContentFront);   
        __quex_assert(buffer->_lexeme_start_p == ContentFront);

        /* end   != 0, means that the buffer is filled.
         * begin == 0, means that we are standing at the begin.
         * => end != 0 and begin == 0, means that the initial content is loaded already.    */
        /* if( buffer->_content_character_index_begin == 0 ) {
         *     if ( buffer->_content_character_index_end != 0) return;
         *} else {*/
        me->seek_character_index(me, 0);
        /*} */
        const size_t  LoadedN = __BufferFiller_read_characters(buffer, ContentFront, ContentSize);

        buffer->_content_character_index_begin = 0; 
        buffer->_content_character_index_end   = (size_t)(me->tell_character_index(buffer->filler));

        if( me->tell_character_index(me) != LoadedN ) 
            QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM);

        /* If end of file has been reached, then the 'end of file' pointer needs to be set. */
        if( LoadedN != ContentSize ) QuexBuffer_end_of_file_set(buffer, ContentFront + LoadedN);
        else                         QuexBuffer_end_of_file_unset(buffer);


        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);
    } 

    QUEX_INLINE size_t
    QuexBufferFiller_load_forward(QuexBuffer* buffer)
    {
        const size_t         ContentSize  = QuexBuffer_content_size(buffer);
        QUEX_TYPE_CHARACTER* ContentFront = QuexBuffer_content_front(buffer);
        /* PURPOSE: This function is to be called as a reaction to a buffer limit code 'BLC'
         *          as returned by 'get_forward()'. Its task is to load new content into the 
         *          buffer such that 'get_forward() can continue iterating. This means that the 
         *          '_input_p' points to one of the following positions:
         *
         *          (1) Beginning of the Buffer: In this case, no reload needs to take place.
         *              It can basically only appear if 'load_forward()' is called after
         *              'get_backward()'---and this does not make sense. But returning a '0'
         *              (which is >= 0 and indicates that everything is ok) tells the application 
         *              that nothing has been loaded, and the next 'get_forward()' will work 
         *              normally.
         *
         *          (2) End of File Pointer: (which may be equal to the end of the buffer) 
         *              In this case no further content can be loaded. The function returns '0'.
         *
         *          (3) End of Buffer (if it is != End of File Pointer): Here a 'normal' load of
         *              new data into the buffer can happen.
         *
         * RETURNS: '>= 0'   number of characters that were loaded forward in the stream.
         *          '-1'     if forward loading was not possible (end of file)                      */
        /* 
         * NOTE: There is a seemingly dangerous case where the loading **just** fills the buffer to 
         *       the limit. In this case no 'End Of File' is detected, no end of file pointer is set,
         *       and as a consequence a new loading will happen later. This new loading, though,
         *       will only copy the fallback-region. The 'LoadedN == 0' will cause the _memory._end_of_file_p
         *       to be set to the end of the copied fallback-region. And everything is fine.
         */
        QuexBufferFiller*  me = buffer->filler;
        if( me == 0x0 ) return 0; /* This case it totally rational, if no filler has been specified */

        __quex_assert(buffer != 0x0);
        __quex_assert(me->tell_character_index != 0x0);
        __quex_assert(me->seek_character_index != 0x0);
        __quex_assert(me->read_characters != 0x0);

        /* Catch impossible scenario: If the stretch from _input_p to _lexeme_start_p 
         * spans the whole buffer content, then nothing can be loaded into it.                      */
        const size_t Distance_LexemeStart_to_InputP = buffer->_input_p - buffer->_lexeme_start_p;
        if( Distance_LexemeStart_to_InputP >= ContentSize ) { 
            __QuexBufferFiller_on_overflow(buffer, /* Forward */ true);
            return 0;
        }
        QUEX_DEBUG_PRINT_BUFFER_LOAD(buffer, "FORWARD(entry)");

        /* (*) Check for the three possibilities mentioned above */
        if     ( buffer->_input_p == buffer->_memory._front )         { return 0; }   /* (1)*/
        else if( buffer->_input_p == buffer->_memory._end_of_file_p ) { return 0; }   /* (2)*/
        else if( buffer->_input_p != buffer->_memory._back  ) {                     
            QUEX_ERROR_EXIT("Call to 'load_forward() but '_input_p' not on buffer border.\n" 
                            "(Check character encoding)");  
        }
        else if( buffer->_memory._end_of_file_p != 0x0 ) { 
            /* End of file has been reached before, we cannot load more.                    */
            return 0;                               
        }
        /* HERE: _input_p ---> LAST ELEMENT OF THE BUFFER!                             * (3)*/  


        /*___________________________________________________________________________________*/
        /* (1) Handle fallback region */
        const size_t  FallBackN = __QuexBufferFiller_forward_compute_fallback_region(buffer, 
                                                                                     Distance_LexemeStart_to_InputP);
        const size_t  DesiredLoadN = ContentSize - FallBackN;
        __quex_assert(FallBackN < ContentSize);
        __QuexBufferFiller_forward_copy_fallback_region(buffer, FallBackN);

        /*___________________________________________________________________________________*/
        /* (2) Load new content*/
        /* NOTE: Due to backward loading the character index might not stand on the end of
         *       the buffer. Thus a seek is necessary.                                       */
        me->seek_character_index(me, buffer->_content_character_index_end);
        buffer->_content_character_index_begin = buffer->_content_character_index_end - FallBackN;

        QUEX_TYPE_CHARACTER* new_content_begin = ContentFront + FallBackN;
        const size_t         LoadedN           =  __BufferFiller_read_characters(buffer, new_content_begin, DesiredLoadN);
        
        /*___________________________________________________________________________________*/
        /* (3) Adapt the pointers in the buffer*/
        __QuexBufferFiller_forward_adapt_pointers(buffer, 
                                                  DesiredLoadN, LoadedN, FallBackN, 
                                                  Distance_LexemeStart_to_InputP);

        buffer->_content_character_index_end   =   buffer->_content_character_index_begin
                                                 + (QuexBuffer_text_end(buffer) - ContentFront);

        /* If the character index in the stream is different from 'old index + LoadedN'
         * then this indicates a 'strange stream' where the stream position increment is
         * not proportional to the number of loaded characters.                              */
        if( (size_t)(me->tell_character_index(me) - buffer->_content_character_index_begin) - FallBackN != LoadedN ) 
            QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM);

        QUEX_DEBUG_PRINT_BUFFER_LOAD(buffer, "LOAD FORWARD(exit)");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);
        /* NOTE: Return value is used for adaptions of memory addresses. It happens that the*/
        /*       address offset is equal to DesiredLoadN; see function __forward_adapt_pointers().*/
        return DesiredLoadN; /* THUS NOT: LoadedN*/
    }

    QUEX_INLINE size_t
    __QuexBufferFiller_forward_compute_fallback_region(QuexBuffer*  buffer,
                                                       const size_t Distance_LexemeStart_to_InputP)
    {
        /* (1) Fallback: A certain region of the current buffer is copied in front such that
         *               if necessary the stream can go backwards without a backward load.
         *
         *                            fallback_n
         *                               :
         *                |11111111111111:22222222222222222222222222222222222222|
         *                  copy of      :   new loaded content of buffer
         *                  end of old   
         *                  buffer      
         *
         *     The fallback region is related to the lexeme start pointer. The lexeme start 
         *     pointer always needs to lie inside the buffer, because applications might read
         *     their characters from it. The 'stretch' [lexeme start, current_p] must be 
         *     contained in the new buffer (precisely in the fallback region).                        */
        /* Copying forward shall **only** happen when new content is to be loaded. This is not the case
         * if EOF is reached and the _memory._memory._end_of_file_p lies inside the buffer. Thus the _input_p
         * must have reached the upper border of the buffer.                                          */
        __quex_assert(buffer->_memory._end_of_file_p == 0x0);
        __quex_assert(buffer->_input_p == buffer->_memory._back);
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        __quex_assert((int)Distance_LexemeStart_to_InputP == buffer->_input_p - buffer->_lexeme_start_p);
        __quex_assert(Distance_LexemeStart_to_InputP < QuexBuffer_content_size(buffer));

        /* (*) Fallback region = max(default size, necessary size)*/
        const size_t FallBackN = QUEX_SETTING_BUFFER_MIN_FALLBACK_N > Distance_LexemeStart_to_InputP 
                                 ? QUEX_SETTING_BUFFER_MIN_FALLBACK_N  
                                 : Distance_LexemeStart_to_InputP;
        return FallBackN;
    }

    QUEX_INLINE void
    __QuexBufferFiller_forward_copy_fallback_region(QuexBuffer* buffer, const size_t FallBackN)
    {
        /* (*) Copy fallback region*/
        /*     If there is no 'overlap' from source and drain than the faster memcpy() can */
        /*     used instead of memmove().*/
        QUEX_TYPE_CHARACTER*  source = QuexBuffer_content_back(buffer) - FallBackN + 1; /* end of content - fallback*/
        QUEX_TYPE_CHARACTER*  drain  = QuexBuffer_content_front(buffer);       
        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        if( drain + FallBackN >= source  ) {
            __QUEX_STD_memmove((uint8_t*)drain, (uint8_t*)source, FallBackN * sizeof(QUEX_TYPE_CHARACTER));
        } else { 
            __QUEX_STD_memcpy((uint8_t*)drain, (uint8_t*)source, FallBackN * sizeof(QUEX_TYPE_CHARACTER));
        }

#       ifdef QUEX_OPTION_ASSERTS
        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        __QUEX_STD_memset((uint8_t*)(drain + FallBackN), (uint8_t)(0xFF), 
                          (QuexBuffer_content_size(buffer) - FallBackN)*sizeof(QUEX_TYPE_CHARACTER)); 
#       endif

        __quex_assert(FallBackN < QuexBuffer_content_size(buffer));
    }

    QUEX_INLINE void
    __QuexBufferFiller_forward_adapt_pointers(QuexBuffer*  buffer, 
                                              const size_t DesiredLoadN,
                                              const size_t LoadedN,
                                              const size_t FallBackN, 
                                              const size_t Distance_LexemeStart_to_InputP)
    {
#       ifdef QUEX_OPTION_ASSERTS
        const size_t         ContentSize  = QuexBuffer_content_size(buffer);
#       endif
        QUEX_TYPE_CHARACTER* ContentFront = QuexBuffer_content_front(buffer);

        __quex_assert( buffer->_memory._end_of_file_p == 0x0 || LoadedN + FallBackN == ContentSize );
        __quex_assert( DesiredLoadN != 0 );

        /* (*) If end of file has been reached, then the 'end of file' pointer needs to be set*/
        if( LoadedN != DesiredLoadN ) 
            QuexBuffer_end_of_file_set(buffer, ContentFront + FallBackN + LoadedN);
        else
            QuexBuffer_end_of_file_unset(buffer);

        /*___________________________________________________________________________________*/
        /* (*) Pointer adaption*/
        /*     Next char to be read: '_input_p + 1'*/
        buffer->_input_p        = ContentFront + FallBackN - 1;   
        /*     NOTE: _input_p is set to (_input_p - 1) so that the next *(++_input_p) */
        /*           reads the _input_p.*/
        buffer->_lexeme_start_p = (buffer->_input_p + 1) - Distance_LexemeStart_to_InputP; 

        /* Asserts */
        __quex_assert(   buffer->_memory._end_of_file_p == 0x0 
                      || (int)(LoadedN + FallBackN) == buffer->_memory._end_of_file_p - buffer->_memory._front - 1);

    }


    QUEX_INLINE size_t   
    QuexBufferFiller_load_backward(QuexBuffer* buffer)
    {
        QuexBufferFiller* me = buffer->filler;
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        if( me == 0x0 ) return 0; /* This case it totally rational, if no filler has been specified */

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
        QUEX_TYPE_CHARACTER*   ContentFront = QuexBuffer_content_front(buffer);
        QUEX_TYPE_CHARACTER*   ContentBack  = QuexBuffer_content_back(buffer);

        QUEX_DEBUG_PRINT_BUFFER_LOAD(buffer, "BACKWARD(entry)");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

        /* (*) Check for the three possibilities mentioned above*/
        if     ( buffer->_input_p == buffer->_memory._back )  { return 0; }   /* (1) */
        else if( buffer->_input_p == buffer->_memory._end_of_file_p ) { return 0; }   /* (1) */
        else if( buffer->_input_p != buffer->_memory._front ) {
            QUEX_ERROR_EXIT("Call to 'load_backward() but '_input_p' not on buffer border.\n" 
                            "(Check character encoding)");  
        }
        else if( buffer->_content_character_index_begin == 0 ) { return 0; }  /* (2) */
        /*                                                                     * (3) */
        /* HERE: current_p == FRONT OF THE BUFFER!   
         *_______________________________________________________________________________*/
        /* Catch impossible scenario: If the stretch from _input_p to _lexeme_start_p 
         * spans the whole buffer content, then nothing can be loaded into it.           */
        if( buffer->_lexeme_start_p == ContentBack ) { 
            __QuexBufferFiller_on_overflow(buffer, /* ForwardF */ false);
            return 0;
        }

        /*_______________________________________________________________________________
         * (1) Compute distance to go backwards */
        const size_t  BackwardDistance = __QuexBufferFiller_backward_compute_backward_distance(buffer);
        /*_______________________________________________________________________________
         * (2) Compute the stream position of the 'start to read'   
         *  
         * It is not safe to assume that the character size is fixed. Thus it is up to  
         * the input strategy to determine the input position that belongs to a character  
         * position. */
        const size_t  NewContentCharacterIndexBegin = buffer->_content_character_index_begin - BackwardDistance;
        __quex_assert(BackwardDistance != 0); /* if "_index_begin != 0", then backward load must be. */
        me->seek_character_index(me, NewContentCharacterIndexBegin);

        /*_______________________________________________________________________________
         * (3) Load content*/
        buffer->_content_character_index_begin = NewContentCharacterIndexBegin;
        __QuexBufferFiller_backward_copy_backup_region(buffer, BackwardDistance);
        
        /* -- If file content < buffer size, then the start position of the stream to which  
         *    the buffer refers is always 0 and no backward loading will ever happen.  
         * -- If the file content >= buffer size, then backward loading must always fill  
         *    the buffer. */
        const size_t LoadedN = __BufferFiller_read_characters(buffer, ContentFront, BackwardDistance);
        __quex_assert(LoadedN == (size_t)BackwardDistance);

        /*________________________________________________________________________________
         * (4) Adapt pointers */
        __QuexBufferFiller_backward_adapt_pointers(buffer, BackwardDistance);

        buffer->_content_character_index_end =   buffer->_content_character_index_begin
                                               + (QuexBuffer_text_end(buffer) - ContentFront);
        /* If the character index in the stream is different from 'old index + LoadedN'
         * then this indicates a 'strange stream' where the stream position increment is
         * not proportional to the number of loaded characters.                              */
        if( (size_t)(me->tell_character_index(me) - buffer->_content_character_index_begin) != LoadedN ) 
            QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM);

        QUEX_DEBUG_PRINT_BUFFER_LOAD(buffer, "BACKWARD(exit)");
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(buffer);

        return BackwardDistance;
    }


    QUEX_INLINE size_t
    __QuexBufferFiller_backward_compute_backward_distance(QuexBuffer* buffer)
    {
        const size_t         ContentSize  = QuexBuffer_content_size(buffer);

        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        /* Copying backward shall **only** happen when new content is to be loaded. In back
         * ward direction, this makes only sense if the lower border was reached.         */
        __quex_assert(buffer->_input_p == buffer->_memory._front);
        /* Also, if the lower border is the begin of file, then there is no sense in
         * loading more in backward direction.                                            */
        __quex_assert(buffer->_content_character_index_begin != 0);
        /* We need to make sure, that the lexeme start pointer remains inside the
         * buffer, so that we do not loose the reference. From current_p == buffer begin
         * it is safe to say that _lexeme_start_p > _input_p (the lexeme starts
         * on a letter not the buffer limit).                                             */
        __quex_assert(buffer->_lexeme_start_p > buffer->_input_p);
        __quex_assert((size_t)(buffer->_lexeme_start_p - buffer->_input_p) < QuexBuffer_content_size(buffer));

        const size_t IntendedBackwardDistance = ContentSize > (size_t)3 ? (size_t)(ContentSize / 3) 
                                                :                         (size_t)1;   
        /* IntendedBackwardDistance > 0 */

        /* Limit 1:
         *
         *     Before:    |C      L                  |
         *
         *     After:     |       C      L           |
         *                 ------->
         *                 backward distance
         *
         *     Lexeme start pointer L shall lie inside the buffer. Thus, it is required:
         *
         *               LimitBackwardDist_1 + (C - L) < size
         *           =>            LimitBackwardDist_1 < size - (C - L)
         *            
         *           =>  LimitBackwardDist_1 > 0, see __quex_assert(...) above. */
        const size_t Distance_InputP_to_LexemeStart = (size_t)(buffer->_lexeme_start_p - buffer->_input_p);
        const int    LimitBackwardDist_1            = ContentSize - Distance_InputP_to_LexemeStart; 

        /* Limit 2:
         *     We cannot go before the first character in the stream. 
         *         LimitBackwardDist_2 > 0, see __quex_assert(...) above. */
        const int    LimitBackwardDist_2 = (int)buffer->_content_character_index_begin;


        /* Taking the minimum of all:*/
        /*           Limit_1_and_2 = min(LimitBackwardDist_1 and _2) > 0 */
        const size_t Limit_1_and_2 = LimitBackwardDist_1 < LimitBackwardDist_2 ? LimitBackwardDist_1
                                     :                                           LimitBackwardDist_2;

        const size_t BackwardDistance = IntendedBackwardDistance < Limit_1_and_2 ?  IntendedBackwardDistance 
                                        :                                           Limit_1_and_2;

        __quex_assert(BackwardDistance > 0);
        return BackwardDistance;
    }

    QUEX_INLINE void
    __QuexBufferFiller_backward_copy_backup_region(QuexBuffer* buffer, const size_t BackwardDistance)
    {
        const size_t         ContentSize      = QuexBuffer_content_size(buffer);
        QUEX_TYPE_CHARACTER* ContentFront     = QuexBuffer_content_front(buffer);

        /* (*) copy content that is already there to its new position.
         *     (copying is much faster then loading new content from file). */
        __QUEX_STD_memmove(ContentFront + BackwardDistance, ContentFront, 
                           (ContentSize - BackwardDistance)*sizeof(QUEX_TYPE_CHARACTER));

#       ifdef QUEX_OPTION_ASSERTS
        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        __QUEX_STD_memset((uint8_t*)ContentFront, (uint8_t)(0xFF), BackwardDistance * sizeof(QUEX_TYPE_CHARACTER)); 
#       endif
    }

    QUEX_INLINE void
    __QuexBufferFiller_backward_adapt_pointers(QuexBuffer* buffer, const size_t BackwardDistance)
    {
        /* -- end of file / end of buffer:*/
        if( buffer->_memory._end_of_file_p ) {
            QUEX_TYPE_CHARACTER*   NewEndOfFileP = buffer->_memory._end_of_file_p + BackwardDistance;
            if( NewEndOfFileP <= buffer->_memory._back ) 
                QuexBuffer_end_of_file_set(buffer, NewEndOfFileP);
            else  
                QuexBuffer_end_of_file_unset(buffer);
        }

        buffer->_input_p        += BackwardDistance + 1; 
        buffer->_lexeme_start_p += BackwardDistance;
    }

    QUEX_INLINE void
    __QuexBufferFiller_on_overflow(QuexBuffer* buffer, bool ForwardF)
    {
        QuexBufferFiller* me = buffer->filler;

        if(    me->_on_overflow == 0x0
            || me->_on_overflow(buffer, ForwardF) == false ) {

#           ifdef QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE
            /* Print out the lexeme start, so that the user has a hint. */
            uint8_t               utf8_encoded_str[512]; 
            static char           message[1024];
            const size_t          MessageSize = 1024;
            uint8_t*              WEnd        = utf8_encoded_str + 512 - 7;
            uint8_t*              witerator   = utf8_encoded_str; 
            QUEX_TYPE_CHARACTER*  End         = buffer->_memory._back; 
            QUEX_TYPE_CHARACTER*  iterator    = buffer->_lexeme_start_p; 
            size_t                utf8_length = (size_t)0;
            
            for(; witerator < WEnd &&  iterator != End ; ++iterator) {
                utf8_length = Quex_unicode_to_utf8(*iterator, witerator);
                if( utf8_length < (size_t)0 || utf8_length > (size_t)6) continue;
                witerator += utf8_length;
                *witerator = '\0';
            }
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
                            "size to a greate value or use skippers (<skip: [ \n\t]> for example.");
#           endif /* QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE */
        }
    }

    QUEX_INLINE void 
    __QuexBufferFiller_step_forward_n_characters(QuexBufferFiller* me,
                                                 const size_t      ForwardN)
    { 
        /* STRATEGY: Starting from a certain point in the file we read characters
         *           Convert one-by-one until we reach the given character index. 
         *           This is, of course, incredibly inefficient but safe to work under
         *           all circumstances. Fillers should only rely on this function
         *           in case of no other alternative. Also, caching some information 
         *           about what character index is located at what position may help
         *           to increase speed.                                                */      
        __quex_assert(QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE >= 1);

#       ifdef QUEX_OPTION_ASSERTS
        const size_t         TargetIndex = me->tell_character_index(me) + ForwardN;
#       endif

        /* START: We are now at character index 'CharacterIndex - remaining_character_n'.
         * LOOP:  It remains to interpret 'remaining_character_n' number of characters. Since 
         *        the interpretation is best done using a buffer, we do this in chunks.      */ 
        size_t               remaining_character_n = ForwardN;
        const size_t         ChunkSize = QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE;
        QUEX_TYPE_CHARACTER  chunk[QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE];

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

    QUEX_INLINE size_t       
    __BufferFiller_read_characters(QuexBuffer*           buffer, 
                                   QUEX_TYPE_CHARACTER*  memory, const size_t MemorySize)
    {
        const size_t  LoadedN = buffer->filler->read_characters(buffer->filler, memory, MemorySize);

        if( buffer->_byte_order_reversion_active_f ) {
            QuexBuffer_reverse_byte_order(memory, memory + LoadedN);
        }
        return LoadedN;
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

