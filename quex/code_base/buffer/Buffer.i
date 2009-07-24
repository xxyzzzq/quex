/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__

#include <quex/code_base/asserts>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/MemoryManager>

#include <quex/code_base/temporary_macros_on>

#ifndef    QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW 
#   define QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW  0x0
#endif

#if ! defined(__QUEX_SETTING_PLAIN_C)
namespace quex { 
#endif

    QUEX_INLINE void  QuexBuffer_init(QuexBuffer*  me, bool OnlyResetF); 
    QUEX_INLINE void  QuexBufferMemory_init(QuexBufferMemory*    me, 
                                            QUEX_TYPE_CHARACTER* memory, size_t Size);

    TEMPLATE_IN(InputHandleT) void
    QuexBuffer_construct(QuexBuffer*           me, 
                         InputHandleT*         input_handle,
                         QUEX_TYPE_CHARACTER*  InputMemory,
                         const size_t          MemorySize,
                         const char*           CharacterEncodingName, 
                         const size_t          TranslationBufferMemorySize)
        /* The input can either come from MEMORY or from a STREAM. 
         *
         * input_handle == 0x0 => input via memory
         *              != 0x0 => input via stream (spec. by input_handle)
         *
         * InputMemory != 0x0  => run directly on specified memory.
         *             == 0x0  => get memory from memory manager.           */ 
    {
        QUEX_TYPE_CHARACTER* memory = InputMemory;
        __quex_assert(MemorySize > 2);
#       ifdef QUEX_OPTION_ASSERTS
        if( input_handle != 0x0 ) __quex_assert(InputMemory == 0x0 );
        if( InputMemory  != 0x0 ) { 
            __quex_assert(input_handle == 0x0 );
            /* If the input memory is provided, the content **must** be propperly set up. */
            QUEX_BUFFER_ASSERT_NO_BUFFER_LIMIT_CODE(InputMemory + 1, InputMemory + MemorySize - 1);
        }
#       endif

        if( memory == 0x0 ) memory = MemoryManager_BufferMemory_allocate(MemorySize);

        QuexBufferMemory_init(&(me->_memory), memory, MemorySize);      

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
            me->filler = (QuexBufferFiller*)QuexBufferFiller_Converter_new(input_handle, 
                                  QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW,
                                  CharacterEncodingName, /* Internal Coding: Default */0x0,
                                  TranslationBufferMemorySize);
       
        } else {
            /* If no converter is required, it has to be considered whether the buffer needs
             * filling or not. If the input source is not memory, then the 'plain' buffer
             * filling is applied. If the input source is memory, no filler is required.   */
            me->filler = (input_handle == 0x0) ? 0x0 : (QuexBufferFiller*)QuexBufferFiller_Plain_new(input_handle);
        }

        if( InputMemory != 0x0 ) {
            me->_memory_has_external_owner_f = true;
            /* Assume by default, that the memory is filled up to the limit. If this is not
             * the case, the value must be adapted.                                         */
            QuexBuffer_end_of_file_set(me, me->_memory._back);
        } else {
            me->_memory_has_external_owner_f = false;
            QuexBuffer_end_of_file_unset(me);
        }
        
        QuexBuffer_init(me, /* OnlyResetF */ false);

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me);
    }


    QUEX_INLINE void
    QuexBuffer_destruct(QuexBuffer* me)
    {
        if( me->filler != 0x0 ) me->filler->_destroy(me->filler); 

        if( me->_memory_has_external_owner_f == false ) 
            MemoryManager_BufferMemory_free(me->_memory._front);
    }

    QUEX_INLINE void
    QuexBuffer_init(QuexBuffer*  me, bool ResetF)
    {
        me->_input_p        = me->_memory._front + 1;  /* First State does not increment */
        me->_lexeme_start_p = me->_memory._front + 1;  /* Thus, set it on your own.      */
        /* NOTE: The terminating zero is stored in the first character **after** the  
         *       lexeme (matching character sequence). The begin of line pre-condition  
         *       is concerned with the last character in the lexeme, which is the one  
         *       before the 'char_covered_by_terminating_zero'.                          */
        me->_character_at_lexeme_start     = '\0';  /* (0 means: no character covered)   */
        me->_content_character_index_end   = 0;
#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = '\n';  /* --> begin of line                 */
#       endif

        if( me->filler != 0x0 ) {
            if( ResetF ) {
                /* We only have to reset the input stream, if we are not at position zero */
                if( me->_content_character_index_begin != 0 ) {
                    __quex_assert(me->filler != 0x0);
                    me->filler->seek_character_index(me->filler, 0);
                    me->_content_character_index_begin = 0; /* Cannot be (re-)initialized earlier, see above) */
                    QuexBufferFiller_initial_load(me);      /* _content_character_index_begin == 0 in assert  */
                } else {
                    /* In the reset case, the end of file pointer has to remain, if no reload happens.        */
                }
            } else {
                /* If a real buffer filler is specified, then fill the memory. Otherwise, one 
                 * assumes, that the user fills/has filled it with whatever his little heart desired.         */
                me->_content_character_index_begin = 0;     /* Cannot be (re-)initialized earlier, see above. */
                QuexBufferFiller_initial_load(me);
            }
        }
        me->_content_character_index_begin = 0; /* Cannot be (re-)initialized earlier, see above)             */

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me);
    }

    QUEX_INLINE void
    QuexBuffer_reset(QuexBuffer* me)
    {
        QuexBuffer_init(me, /* ResetF */ true);
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
    QuexBufferMemory_init(QuexBufferMemory* me, 
                          QUEX_TYPE_CHARACTER* memory, size_t Size) 
    {
        /* The buffer memory can be initially be set to '0x0' if no buffer filler
         * is specified. Then the user has to call this function on his own in order
         * to specify the memory on which to rumble. */
        __quex_assert((Size != 0) || (memory == 0x0)); 

        if( Size == 0 ) { 
            me->_front = me->_back = 0;
            return;
        }
        /* Min(Size) = 2 characters for buffer limit code (front and back) + at least
         * one character to be read in forward direction. */
        __quex_assert(Size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2);
        me->_front    = memory;
        me->_back     = memory + (Size - 1);
        /* NOTE: We cannot set the memory all to zero at this point in time. It may be that the
         *       memory is already filled with content (e.g. by an external owner). The following
         *       code has deliberately be disabled:
         *           #ifdef QUEX_OPTION_ASSERTS
         *           __QUEX_STD_memset(me->_front, 0, Size);
         *           #endif 
         *       When the buffer uses a buffer filler, then it is a different ball game. Please,
         *       consider QuexBuffer_init().
         */
        *(me->_front) = QUEX_SETTING_BUFFER_LIMIT_CODE;
        *(me->_back)  = QUEX_SETTING_BUFFER_LIMIT_CODE;
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


#if ! defined(__QUEX_SETTING_PLAIN_C)
} /* namespace quex */
#endif

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/MemoryManager.i>

#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__BUFFER__BUFFER_CORE_I__ */


