/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I

#include <quex/code_base/analyzer/configuration/validation>
#include <quex/code_base/asserts>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/MemoryManager>

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_COMPONENTS_OPEN

    QUEX_INLINE void  QuexBuffer_init(QuexBuffer*  me, bool ByteOrderReversionF); 
    QUEX_INLINE void  QuexBuffer_init_analyzis(QuexBuffer*  me, bool ByteOrderReversionF);
    QUEX_INLINE void  QuexBufferMemory_construct(QuexBufferMemory*    me, 
                                                 QUEX_TYPE_CHARACTER* memory, size_t Size);
    QUEX_INLINE void  QuexBufferMemory_init(QuexBufferMemory*     me, 
                                            QUEX_TYPE_CHARACTER*  InputMemory, size_t  MemorySize);
    QUEX_INLINE void  QuexBufferMemory_destruct(QuexBufferMemory* me);

    TEMPLATE_IN(InputHandleT) void
    QuexBuffer_construct(QuexBuffer*           me, 
                         InputHandleT*         input_handle,
                         QUEX_TYPE_CHARACTER*  InputMemory,
                         const size_t          MemorySize,
                         const char*           CharacterEncodingName, 
                         const size_t          TranslationBufferMemorySize,
                         bool                  ByteOrderReversionF)
        /* The input can either come from MEMORY or from a STREAM. 
         *
         * input_handle == 0x0 => input via memory
         *              != 0x0 => input via stream (spec. by input_handle)
         *
         * InputMemory != 0x0  => run directly on specified memory.
         *             == 0x0  => get memory from memory manager.                              */ 
    {
        __quex_assert(MemorySize > 2);
#       ifdef QUEX_OPTION_ASSERTS
        if( input_handle != 0x0 ) __quex_assert(InputMemory == 0x0 );
        if( InputMemory  != 0x0 ) { 
            __quex_assert(input_handle == 0x0 );
            /* If the input memory is provided, the content **must** be propperly set up.      */
            QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(InputMemory + 1, InputMemory + MemorySize - 1);
        }
#       endif

        /* No allocation of the base 'me->_memory' since it is a plain member of 'QuexBuffer'.
         * InputMemory == 0x0 => interact with memory manager to get memory.                   */
        QuexBufferMemory_construct(&(me->_memory), InputMemory, MemorySize);      

        me->filler = QuexBufferFiller_new(input_handle, CharacterEncodingName, TranslationBufferMemorySize);

        QuexBuffer_init(me, ByteOrderReversionF);

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me);
    }

    QUEX_INLINE void
    QuexBuffer_init(QuexBuffer*  me, bool ByteOrderReversionF)
    {
        /* By setting begin and end to zero, we indicate to the loader that
         * this is the very first load procedure.                           */
        me->_content_character_index_end   = 0;
        me->_content_character_index_begin = 0; 

        QuexBuffer_init_analyzis(me, ByteOrderReversionF);

        if( me->filler != 0x0 ) {
            /* We only have to reset the input stream, if we are not at position zero    */
            QuexBufferFiller_initial_load(me);   
        } 

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me);
    }

    QUEX_INLINE void
    QuexBuffer_init_analyzis(QuexBuffer*  me, bool ByteOrderReversionF)
    {
        me->_byte_order_reversion_active_f = ByteOrderReversionF;

        /* Init is a special kind of reset, where some things might not be reset. */
        me->_input_p        = me->_memory._front + 1;  /* First State does not increment */
        me->_lexeme_start_p = me->_memory._front + 1;  /* Thus, set it on your own.      */
        /* NOTE: The terminating zero is stored in the first character **after** the  
         *       lexeme (matching character sequence). The begin of line pre-condition  
         *       is concerned with the last character in the lexeme, which is the one  
         *       before the 'char_covered_by_terminating_zero'.                          */
        me->_character_at_lexeme_start     = '\0';  /* (0 means: no character covered)   */
#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = '\n';  /* --> begin of line                 */
#       endif
    }

    QUEX_INLINE void
    QuexBuffer_destruct(QuexBuffer* me)
    {
        if( me->filler != 0x0 ) { 
            me->filler->delete_self(me->filler); 
            me->filler = 0x0;
        }

        QuexBufferMemory_destruct(&me->_memory);
    }

    TEMPLATE_IN(InputHandleT) void
    QuexBuffer_reset(QuexBuffer*    me, 
                     InputHandleT*  input_handle, 
                     const char*    CharacterEncodingName, 
                     const size_t   TranslationBufferMemorySize)
    /* NOTE:     me->_content_character_index_begin == 0 
     *       and me->_content_character_index_end   == 0 
     *       => buffer is filled the very first time.                                    
     * NOTE: The reset of the buffer filler happens by 'delete' and 'new'. This is
     *       done in order to keep the template decoupled from the rest. Only the
     *       'new' functions (allocator + constructor) know about the template. The
     *       'delete_self' function pointer is set to a template that knows how to
     *       deallocate the object.
     */
    {
        /* Setup the buffer filler for new analyzis */
        if( me->filler != 0x0 ) { 
            /* If the same input handle is used, as before, than the following command
             * ensures, that we start at the same position.                            */
            me->filler->seek_character_index(me->filler, 0);
            me->filler->delete_self(me->filler);
        }
        me->filler = QuexBufferFiller_new(input_handle, CharacterEncodingName, TranslationBufferMemorySize);

        QuexBuffer_init_analyzis(me, me->_byte_order_reversion_active_f);

        if( me->filler != 0x0 ) {
            /* We only have to reset the input stream, if we are not at position zero    */
            QuexBufferFiller_initial_load(me);   
        } else {
            me->_content_character_index_begin = 0; 
            me->_content_character_index_end   = 0;
        }

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me);
    }

    QUEX_INLINE void
    QuexBuffer_input_p_add_offset(QuexBuffer* buffer, const size_t Offset)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(buffer);
        buffer->_input_p += Offset; 
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(buffer);
    }

    QUEX_INLINE void
    QuexBuffer_input_p_increment(QuexBuffer* buffer)
    { 
        ++(buffer->_input_p); 
    }

    QUEX_INLINE void
    QuexBuffer_input_p_decrement(QuexBuffer* buffer)
    { 
        --(buffer->_input_p); 
    }

    QUEX_INLINE void
    QuexBuffer_mark_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_lexeme_start_p = buffer->_input_p; 
    }

    QUEX_INLINE void
    QuexBuffer_seek_lexeme_start(QuexBuffer* buffer)
    { 
        buffer->_input_p = buffer->_lexeme_start_p;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER_POSITION
    QuexBuffer_tell_memory_adr(QuexBuffer* buffer)
    {
        /* NOTE: We cannot check for general consistency here, because this function 
         *       may be used by the range skippers, and they write possibly something on
         *       the end of file pointer, that is different from the buffer limit code.
         * NOT: QUEX_BUFFER_ASSERT_CONSISTENCY(buffer); */
        QUEX_DEBUG_PRINT2(buffer, "TELL: %i", (int)buffer->_input_p);
#       if      defined (QUEX_OPTION_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        return QUEX_TYPE_CHARACTER_POSITION(buffer->_input_p, buffer->_content_character_index_begin);
#       else
        return (QUEX_TYPE_CHARACTER_POSITION)(buffer->_input_p);
#       endif
    }

    QUEX_INLINE void
    QuexBuffer_seek_memory_adr(QuexBuffer* buffer, QUEX_TYPE_CHARACTER_POSITION Position)
    {
#       if      defined (QUEX_OPTION_ASSERTS) \
           && ! defined(__QUEX_SETTING_PLAIN_C)
        /* Check wether the memory_position is relative to the current start position   
         * of the stream. That means, that the tell_adr() command was called on the  
         * same buffer setting or the positions have been adapted using the += operator.*/
        __quex_assert(Position.buffer_start_position == buffer->_content_character_index_begin);
        buffer->_input_p = Position.address;
#       else
        buffer->_input_p = Position;
#       endif
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER
    QuexBuffer_input_get(QuexBuffer* me)
    {
        QUEX_DEBUG_PRINT_INPUT(me, *(me->_input_p));
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(me);
#       ifdef QUEX_OPTION_ASSERTS
        if( *me->_input_p == QUEX_SETTING_BUFFER_LIMIT_CODE )
            __quex_assert(   me->_input_p == me->_memory._end_of_file_p 
                          || me->_input_p == me->_memory._back || me->_input_p == me->_memory._front);
#       endif
        return *(me->_input_p); 
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER
    QuexBuffer_input_get_offset(QuexBuffer* me, const size_t Offset)
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(me);
        __quex_assert( me->_input_p + Offset > me->_memory._front );
        __quex_assert( me->_input_p + Offset <= me->_memory._back );
        return *(me->_input_p + Offset); 
    }

    QUEX_INLINE void
    QuexBuffer_store_last_character_of_lexeme_for_next_run(QuexBuffer* me)
    { 
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = *(me->_input_p - 1); 
#       endif
    }  

    QUEX_INLINE void
    QuexBuffer_set_terminating_zero_for_lexeme(QuexBuffer* me)
    { 
        me->_character_at_lexeme_start = *(me->_input_p); 
        *(me->_input_p) = '\0';
    }

    QUEX_INLINE void
    QuexBuffer_undo_terminating_zero_for_lexeme(QuexBuffer* me)
    {
        /* only need to reset, in case that the terminating zero was set*/
        if( me->_character_at_lexeme_start != (QUEX_TYPE_CHARACTER)'\0' ) {  
            *(me->_input_p) = me->_character_at_lexeme_start;                  
            me->_character_at_lexeme_start = (QUEX_TYPE_CHARACTER)'\0';     
        }
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QuexBuffer_content_front(QuexBuffer* me)
    {
        return me->_memory._front + 1;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QuexBuffer_content_back(QuexBuffer* me)
    {
        return me->_memory._back - 1;
    }

    QUEX_INLINE size_t
    QuexBuffer_content_size(QuexBuffer* me)
    {
        return QuexBufferMemory_size(&(me->_memory)) - 2;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QuexBuffer_text_end(QuexBuffer* me)
    {
        /* Returns a pointer to the position after the last text content inside the buffer. */
        if( me->_memory._end_of_file_p != 0 ) return me->_memory._end_of_file_p;
        else                                  return me->_memory._back;   
    }

    QUEX_INLINE size_t
    QuexBuffer_distance_input_to_text_end(QuexBuffer* me)
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(me);
        return QuexBuffer_text_end(me) - me->_input_p;
    }

    QUEX_INLINE void
    QuexBuffer_end_of_file_set(QuexBuffer* me, QUEX_TYPE_CHARACTER* Position)
    {
        /* NOTE: The content starts at _front[1], since _front[0] contains 
         *       the buffer limit code. */
        me->_memory._end_of_file_p    = Position;
        *(me->_memory._end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;

        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE void
    QuexBuffer_end_of_file_unset(QuexBuffer* buffer)
    {
        /* If the end of file pointer is to be 'unset' me must assume that the storage as been
         * overidden with something useful. Avoid setting _memory._end_of_file_p = 0x0 while the 
         * position pointed to still contains the buffer limit code.                             */
        buffer->_memory._end_of_file_p = 0x0;
        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE bool 
    QuexBuffer_is_end_of_file(QuexBuffer* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        return buffer->_input_p == buffer->_memory._end_of_file_p;
    }

    QUEX_INLINE bool                  
    QuexBuffer_is_begin_of_file(QuexBuffer* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        if     ( buffer->_input_p != buffer->_memory._front )  return false;
        else if( buffer->_content_character_index_begin != 0 ) return false;
        return true;
    }

    QUEX_INLINE void  
    QuexBuffer_move_forward(QuexBuffer* me, const size_t CharacterN)
    {
       QUEX_BUFFER_ASSERT_CONSISTENCY(me);
       /* Why: __quex_assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N >= 1); ? fschaef 08y11m1d> */

       if( CharacterN < QuexBuffer_distance_input_to_text_end(me) ) {
           /* _input_p + CharacterN < text_end, thus no reload necessary. */
           me->_input_p += CharacterN;
       }
       else {
           /* _input_p + CharacterN >= text_end, thus we need to reload. */
           if( me->filler == 0x0 || me->_memory._end_of_file_p != 0x0 ) {
               me->_input_p = QuexBuffer_text_end(me);  /* No reload possible */
           } else {
               /* Reload until delta is reachable inside buffer. */
               ptrdiff_t delta    = (ptrdiff_t)CharacterN; 
               ptrdiff_t distance = (ptrdiff_t)QuexBuffer_distance_input_to_text_end(me);
               do {
                   delta -= distance;

                   me->_input_p        = me->_memory._back; /* Prepare reload forward. */
                   me->_lexeme_start_p = me->_input_p;
                   if( QuexBufferFiller_load_forward(me) == 0 ) {
                       me->_input_p = QuexBuffer_text_end(me);  /* No reload possible */
                       break;
                   } 
                   /* After loading forward, we need to increment ... the way the game is to be played. */
                   ++(me->_input_p);
                   distance = (ptrdiff_t)QuexBuffer_distance_input_to_text_end(me);

                   if( delta < distance ) {
                       /* _input_p + delta < text_end, thus no further reload necessary. */
                       me->_input_p += delta;
                       break;
                   }
               } while( 1 + 1 == 2 );
           }
       }
       me->_lexeme_start_p            = me->_input_p;
       me->_character_at_lexeme_start = *(me->_lexeme_start_p);
#      ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
       me->_character_before_lexeme_start = *(me->_lexeme_start_p - 1);
#      endif

       QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    }
    
    QUEX_INLINE void  
    QuexBuffer_move_backward(QuexBuffer* me, const size_t CharacterN)
    {
       QUEX_BUFFER_ASSERT_CONSISTENCY(me);

       /* When going backward, anyway a non-zero width distance is left ahead. */
       if( CharacterN < (size_t)(me->_input_p - QuexBuffer_content_front(me)) ) {
           /* _input_p - CharacterN < content_front, thus no reload necessary. */
           me->_input_p -= CharacterN;
       }
       else {
           /* _input_p - CharacterN < _front + 1 >= text_end, thus we need to reload. */
           if( me->filler == 0x0 || me->_content_character_index_begin == 0 ) { 
               me->_input_p = QuexBuffer_content_front(me);
           } else {
               /* Reload until delta is reachable inside buffer. */
               ptrdiff_t delta    = (ptrdiff_t)CharacterN; 
               ptrdiff_t distance = (ptrdiff_t)(me->_input_p - QuexBuffer_content_front(me));
               do {
                   delta -= distance;

                   me->_input_p        = me->_memory._front; /* Prepare reload backward. */
                   me->_lexeme_start_p = me->_input_p + 1;
                   if( QuexBufferFiller_load_backward(me) == 0 ) {
                       me->_input_p = QuexBuffer_content_front(me); /* No reload possible */
                       break;
                   } 
                   /* After loading backwards, we need **not** to increment ... the way the game is to be played. */
                   distance = (ptrdiff_t)(me->_input_p - QuexBuffer_content_front(me));

                   if( delta < distance ) {
                       /* _input_p + delta < text_end, thus no further reload necessary. */
                       me->_input_p -= delta;
                       break;
                   }
               } while( 1 + 1 == 2 );
           }
       }
       me->_lexeme_start_p = me->_input_p;
       me->_character_at_lexeme_start = *(me->_lexeme_start_p);
#      ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
       me->_character_before_lexeme_start = *(me->_lexeme_start_p - 1);
#      endif

       QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    }

    QUEX_INLINE size_t  
    QuexBuffer_tell(QuexBuffer* me)
    {
        /* This function returns the character index that corresponds to the 
         * current setting of the input pointer. Note, that the content starts
         * at one position after the memory (buffer limitting char at _front.).         
         */
        const size_t DeltaToBufferBegin = me->_input_p - me->_memory._front - 1;
        /* Adding the current offset of the content of the buffer in the stream. 
         * If there is no filler, there is no stream, then there is also no offset. */
        if( me->filler == 0x0 ) 
            return DeltaToBufferBegin;
        else
            return DeltaToBufferBegin + me->_content_character_index_begin;
    }

    QUEX_INLINE void    
    QuexBuffer_seek(QuexBuffer* me, const size_t CharacterIndex)
    {
        /* This function sets the _input_p according to a character index of the
         * input stream (if there is a stream). It is the inverse of 'tell()'.   */
        const size_t CurrentCharacterIndex = QuexBuffer_tell(me);
        if( CharacterIndex > CurrentCharacterIndex )
            QuexBuffer_move_forward(me, CharacterIndex - CurrentCharacterIndex);
        else
            QuexBuffer_move_backward(me, CurrentCharacterIndex - CharacterIndex);
    }

    QUEX_INLINE void          
    QuexBuffer_move_away_passed_content(QuexBuffer* me)
    /* PURPOSE: Moves buffer content that has been passed by out of the buffer.
     *
     * Example:  
     *
     *   buffer before: 
     *                         _input_p
     *                            |
     *            [case( x < 10 ) { print; } else ]
     *
     *   buffer after:   
     *              _input_p
     *                 |
     *            [case( x < 10 ) { print; } else ]
     *
     *            |----|
     *         fallback size                                                       */
    { 
        QUEX_TYPE_CHARACTER*  ContentFront      = QuexBuffer_content_front(me);
        QUEX_TYPE_CHARACTER*  RemainderBegin    = me->_input_p;
        QUEX_TYPE_CHARACTER*  RemainderEnd      = me->_memory._end_of_file_p;
        QUEX_TYPE_CHARACTER*  MoveRegionBegin   = RemainderBegin - (ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N;
        size_t                MoveRegionSize    = RemainderEnd - MoveRegionBegin;

        /* Asserts ensure, that we are running in 'buffer-based-mode' */
        __quex_assert(me->_content_character_index_begin == 0); 

        /* If the distance to content front <= the fallback size, no move possible.  */
        if( MoveRegionBegin <= ContentFront ) { return; }

        __QUEX_STD_memmove((void*)ContentFront,
                           (void*)MoveRegionBegin,
                           MoveRegionSize * sizeof(QUEX_TYPE_CHARACTER));


        /* Anything before '_input_p + 1' is considered to be 'past'. However, leave
         * a number of 'FALLBACK' to provide some pre-conditioning to work.          */

        QuexBuffer_end_of_file_set(me, ContentFront + MoveRegionSize);

        /* (*) Pointer adaption:
         *     IMPORTANT: This function is called outside the 'engine' so the 
         *                next char to be read is: '_input_p' not '_input_p + 1'    */
        me->_input_p        = ContentFront + QUEX_SETTING_BUFFER_MIN_FALLBACK_N;   
        /* NOTE: This operation can only happen from outside the lexical analysis
         *       process, i.e. either in a TERMINAL (pattern action) or outside the
         *       receive function calls.                                            */
        me->_lexeme_start_p = me->_input_p; 
    }

    QUEX_INLINE size_t          
    QuexBufferMemory_size(QuexBufferMemory* me)
    { return me->_back - me->_front + 1; }

    QUEX_INLINE void
    __Buffer_reverse_byte_order(QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End)
    {
        uint8_t              tmp = 0xFF;
        QUEX_TYPE_CHARACTER* iterator = 0x0;

        switch( sizeof(QUEX_TYPE_CHARACTER) ) {
        default:
            __quex_assert(false);
            break;
        case 1:
            /* Nothing to be done */
            break;
        case 2:
            for(iterator=Begin; iterator != End; ++iterator) {
                tmp = *(((uint8_t*)iterator) + 0);
                *(((uint8_t*)iterator) + 0) = *(((uint8_t*)iterator) + 1);
                *(((uint8_t*)iterator) + 1) = tmp;
            }
            break;
        case 4:
            for(iterator=Begin; iterator != End; ++iterator) {
                tmp = *(((uint8_t*)iterator) + 0);
                *(((uint8_t*)iterator) + 0) = *(((uint8_t*)iterator) + 3);
                *(((uint8_t*)iterator) + 3) = tmp;
                tmp = *(((uint8_t*)iterator) + 1);
                *(((uint8_t*)iterator) + 1) = *(((uint8_t*)iterator) + 2);
                *(((uint8_t*)iterator) + 2) = tmp;
            }
            break;
        }
    }

    QUEX_INLINE void 
    QuexBufferMemory_construct(QuexBufferMemory* me, 
                               QUEX_TYPE_CHARACTER* InputMemory, size_t Size) 
    {
        if( InputMemory == 0x0 ) { 
            /* The actual 'memory chunk' is an 'owned member resource' accessed by pointer.
             * Thus, it is allocated in the constructor.                                    */
            me->_front = MemoryManager_BufferMemory_allocate(Size);
            QuexBufferMemory_init(me, /* InputMemory */ 0x0, Size); 
        } else { 
            /* The provided memory is externally owned. */
            QuexBufferMemory_init(me, InputMemory, Size); 
        }

    }

    QUEX_INLINE void 
    QuexBufferMemory_init(QuexBufferMemory*     me, 
                          QUEX_TYPE_CHARACTER*  InputMemory, size_t  MemorySize) 
    {
        /* Min(Size) = 2 characters for buffer limit code (front and back) + at least
         * one character to be read in forward direction. */
        __quex_assert(MemorySize > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2);

        if( InputMemory != 0x0 ) {
            /* Assume by default, that the memory is filled up to the limit. If this is not
             * the case, the value must be adapted.                                         */
            me->_front            = InputMemory;
            me->_external_owner_f = true;
            me->_back             = me->_front + (MemorySize - 1);
            me->_end_of_file_p    = me->_back;
        } 
        else {
            /* If the memory is not coming from outside, then it is the task of the con-
             * structor to allocate 'owned' members. It must be assumed that the _front 
             * pointer has been set.                                                        */
#           ifdef QUEX_OPTION_ASSERTS
            __QUEX_STD_memset(me->_front + 1, 0xFF, MemorySize - 2);
#           endif 
            me->_external_owner_f = false;
            me->_end_of_file_p    = 0x0;
            me->_back             = me->_front + (MemorySize - 1);
        }

        *(me->_front) = QUEX_SETTING_BUFFER_LIMIT_CODE;
        *(me->_back)  = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    QUEX_INLINE void 
    QuexBufferMemory_destruct(QuexBufferMemory* me) 
    {
        if( me->_external_owner_f == false && me->_front != (QUEX_TYPE_CHARACTER*)0x0 ) {
            MemoryManager_BufferMemory_free(me->_front);
            me->_external_owner_f = false;
        }

        me->_front = me->_back = (QUEX_TYPE_CHARACTER*)0x0;
    }

    QUEX_INLINE void  
    QuexBuffer_print_this(QuexBuffer* me)
    {
        QUEX_TYPE_CHARACTER*  Offset = me->_memory._front;

        __QUEX_STD_printf("   Buffer:\n");
        __QUEX_STD_printf("      Memory:\n");
        __QUEX_STD_printf("      _front         =  0;\n");
        __QUEX_STD_printf("      _back          = +0x%X;\n", (int)(me->_memory._back - Offset));
        if( me->_memory._end_of_file_p != 0x0 ) 
            __QUEX_STD_printf("      _end_of_file_p = +0x%X;\n", (int)(me->_memory._end_of_file_p - Offset));
        else
            __QUEX_STD_printf("      _end_of_file_p = <void>;\n");

        /* Store whether the memory has an external owner */
        __QUEX_STD_printf("      _external_owner_f = %s;\n", me->_memory._external_owner_f ? "true" : "false");

        __QUEX_STD_printf("   _input_p        = +0x%X;\n", (int)(me->_input_p        - Offset));
        __QUEX_STD_printf("   _lexeme_start_p = +0x%X;\n", (int)(me->_lexeme_start_p - Offset));

        __QUEX_STD_printf("   _character_at_lexeme_start = %X;\n", (int)me->_character_at_lexeme_start);
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        __QUEX_STD_printf("   _character_before_lexeme_start = %X;\n", (int)me->_character_before_lexeme_start);
#       endif
        __QUEX_STD_printf("   _content_character_index_begin = %i;\n", (int)me->_content_character_index_begin);
        __QUEX_STD_printf("   _content_character_index_end   = %i;\n", (int)me->_content_character_index_end);
        __QUEX_STD_printf("   _byte_order_reversion_active_f = %s;\n", me->_byte_order_reversion_active_f ? "true" : "false");
    }

QUEX_NAMESPACE_COMPONENTS_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/MemoryManager.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I */


