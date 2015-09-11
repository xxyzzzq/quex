/* vim:set ft=c: P-*- C++ -*- */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I

#include <quex/code_base/analyzer/configuration/validation>
#include <quex/code_base/asserts>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/MemoryManager>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void  QUEX_NAME(BufferMemory_construct)(QUEX_NAME(BufferMemory)*  me, 
                                                        QUEX_TYPE_CHARACTER*      Memory, 
                                                        const size_t              Size,
                                                        E_Ownership               Ownership);
    QUEX_INLINE void  QUEX_NAME(BufferMemory_destruct)(QUEX_NAME(BufferMemory)* me);

    QUEX_INLINE void
    QUEX_NAME(Buffer_construct)(QUEX_NAME(Buffer)*        me, 
                                QUEX_NAME(BufferFiller)*  filler,
                                QUEX_TYPE_CHARACTER*      memory,
                                const size_t              MemorySize,
                                QUEX_TYPE_CHARACTER*      EndOfFileP,
                                E_Ownership               Ownership)
    {
        /* Ownership of InputMemory is passed to 'me->_memory'.              */
        QUEX_NAME(BufferMemory_construct)(&me->_memory, memory, MemorySize, 
                                          Ownership); 
        
        me->on_buffer_content_change = (void (*)(const QUEX_TYPE_CHARACTER*, const QUEX_TYPE_CHARACTER*))0;

        /* Until now, nothing is loaded into the buffer.                     */

        /* By setting begin and end to zero, we indicate to the loader that
         * this is the very first load procedure.                            */
        me->filler = filler;
        QUEX_NAME(Buffer_init_analyzis)(me, EndOfFileP);
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_init_analyzis)(QUEX_NAME(Buffer)*   me, 
                                    QUEX_TYPE_CHARACTER* EndOfFileP) 
    {
        __quex_assert( ! EndOfFileP || (EndOfFileP > me->_memory._front && EndOfFileP <= me->_memory._back));
        /* (1) BEFORE LOAD: The pointers must be defined which restrict the 
         *                  fill region. 
         *
         * The first state in the state machine does not increment. Thus, the
         * input pointer is set to the first position, not before.           */
        me->_input_p        = &me->_memory._front[1];  
        me->_lexeme_start_p = &me->_memory._front[1];  

        /* The terminating zero is stored in the first character **after** the
         * lexeme (matching character sequence). The begin of line
         * pre-condition  is concerned with the last character in the lexeme,
         * which is the one  before the 'char_covered_by_terminating_zero'.  */
        me->_character_at_lexeme_start = '\0';  /* 0 => no character covered */

#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = QUEX_SETTING_CHARACTER_NEWLINE_IN_ENGINE_CODEC;  /* --> begin of line     */
#       endif

        /* (2) Load content, determine character indices of borders, determine
         *     end of file pointer.                                          */
        if( me->filler && me->filler->byte_loader ) {
            __quex_assert(! EndOfFileP);
            QUEX_NAME(BufferFiller_initial_load)(me);   
            /* Fills buffer and sets: _content_character_index_end
             *                        _memory._end_of_file_p                 */
        } 
        else {
            me->_memory._end_of_file_p       =   EndOfFileP ? EndOfFileP 
                                               : &me->_memory._front[1];
            me->_content_character_index_end =   me->_memory._end_of_file_p 
                                               - &me->_memory._front[1];
        }

        if( me->_memory._end_of_file_p ) {
            *(me->_memory._end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
            QUEX_IF_ASSERTS_poison(&me->_memory._end_of_file_p[1], 
                                   me->_memory._back);
        }
        *(me->_memory._back) = QUEX_SETTING_BUFFER_LIMIT_CODE;

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        /* NOT YET: QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY(me)               */
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_destruct)(QUEX_NAME(Buffer)* me)
    {
        QUEX_NAME(BufferFiller_delete)(&me->filler); 
        QUEX_NAME(BufferMemory_destruct)(&me->_memory);
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_input_p_add_offset)(QUEX_NAME(Buffer)* buffer, const size_t Offset)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(buffer);
        buffer->_input_p += Offset; 
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER
    QUEX_NAME(Buffer_input_get_offset)(QUEX_NAME(Buffer)* me, const ptrdiff_t Offset)
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(me);
        __quex_assert( me->_input_p + Offset > me->_memory._front );
        __quex_assert( me->_input_p + Offset <= me->_memory._back );
        return *(me->_input_p + Offset); 
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_NAME(Buffer_content_front)(QUEX_NAME(Buffer)* me)
    {
        return me->_memory._front + 1;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_NAME(Buffer_content_back)(QUEX_NAME(Buffer)* me)
    {
        return me->_memory._back - 1;
    }

    QUEX_INLINE size_t
    QUEX_NAME(Buffer_content_size)(QUEX_NAME(Buffer)* me)
    {
        return QUEX_NAME(BufferMemory_size)(&(me->_memory)) - 2;
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER*  
    QUEX_NAME(Buffer_text_end)(QUEX_NAME(Buffer)* me)
    {
        /* Returns a pointer to the position after the last text content inside the buffer. */
        if( me->_memory._end_of_file_p ) return me->_memory._end_of_file_p;
        else                             return me->_memory._back;   
    }

    QUEX_INLINE ptrdiff_t
    QUEX_NAME(Buffer_distance_input_to_text_end)(QUEX_NAME(Buffer)* me)
    {
        QUEX_BUFFER_ASSERT_CONSISTENCY_LIGHT(me);
        return QUEX_NAME(Buffer_text_end)(me) - me->_input_p;
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_end_of_file_set)(QUEX_NAME(Buffer)* me, QUEX_TYPE_CHARACTER* Position)
    {
        /* NOTE: The content starts at _front[1], since _front[0] contains 
         *       the buffer limit code. */
        me->_memory._end_of_file_p    = Position;
        *(me->_memory._end_of_file_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;

        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_end_of_file_unset)(QUEX_NAME(Buffer)* buffer)
    {
        /* If the end of file pointer is to be 'unset' me must assume that the storage as been
         * overidden with something useful. Avoid setting _memory._end_of_file_p = 0x0 while the 
         * position pointed to still contains the buffer limit code.                             */
        buffer->_memory._end_of_file_p = 0x0;
        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE bool 
    QUEX_NAME(Buffer_is_end_of_file)(QUEX_NAME(Buffer)* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        return buffer->_input_p == buffer->_memory._end_of_file_p;
    }

    QUEX_INLINE bool                  
    QUEX_NAME(Buffer_is_begin_of_file)(QUEX_NAME(Buffer)* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        if     ( buffer->_input_p != buffer->_memory._front )           return false;
        else if( QUEX_NAME(Buffer_character_index_begin)(buffer) != 0 ) return false;
        return true;
    }

    QUEX_INLINE ptrdiff_t        
    QUEX_NAME(Buffer_move_away_passed_content)(QUEX_NAME(Buffer)* me)
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
     *         fallback size                                                 */
    { 
        const QUEX_TYPE_CHARACTER*  FrontP        = &me->_memory._front[1];
        const QUEX_TYPE_CHARACTER*  BackP         = me->_memory._back;
        const QUEX_TYPE_CHARACTER*  RemainderP    =   me->_lexeme_start_p ? 
                                                      QUEX_MIN(me->_input_p, me->_lexeme_start_p)
                                                    : me->_input_p; 
        const QUEX_TYPE_CHARACTER*  RemainderEndP =   me->_memory._end_of_file_p ? 
                                                      me->_memory._end_of_file_p 
                                                    : me->_memory._back;
        QUEX_TYPE_CHARACTER*  move_begin_p;
        size_t                move_size;
        ptrdiff_t             move_distance;

        /* If distance to content front <= fallback size, no move possible.  */
        if( RemainderP < &FrontP[(ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N] ) {
            return (ptrdiff_t)0;
        }

        move_begin_p  = &RemainderP[- (ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N];
        move_size     = (ptrdiff_t)(RemainderEndP - move_begin_p);
        move_distance = move_begin_p - FrontP;

        /* Anything before '_input_p + 1' is considered to be 'past'. However,
         * leave a number of 'FALLBACK' to provide some pre-conditioning to
         * work.                                                             */
        __QUEX_STD_memmove((void*)FrontP, (void*)move_begin_p,
                           move_size * sizeof(QUEX_TYPE_CHARACTER));

        me->_input_p -= move_distance;
        if( me->_memory._end_of_file_p ) {
            me->_memory._end_of_file_p -= move_distance;
        }
        if( me->_lexeme_start_p ) {
            me->_lexeme_start_p -= move_distance;
        }

        QUEX_IF_ASSERTS_poison((void*)&BackP[-move_distance], (void*)BackP);
        return move_distance;
    }

    QUEX_INLINE ptrdiff_t        
    QUEX_NAME(Buffer_move_away_upfront_content)(QUEX_NAME(Buffer)* me)
    {
        const QUEX_TYPE_CHARACTER*       FrontP       = &me->_memory._front[1];
        const ptrdiff_t                  ContentSize  = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
        const QUEX_TYPE_STREAM_POSITION  CharacterIndexBegin = QUEX_NAME(Buffer_character_index_begin)(me));
        ptrdiff_t                        move_distance;
        ptrdiff_t                        move_size;
        ptrdiff_t                        offset_ls; 
   
        /* Move at least 1 byte backward: distance >= 1                      */
        move_distance = QUEX_MAX((ptrdiff_t)(ContentSize / 3), 1); 
        /* Cannot go before the first character in the stream.               */
        move_distance = QUEX_MIN(move_distance, CharacterIndexBegin);
        /* Lexeme start not beyond back => distance < lexeme_start_p - front */
        if( me->_lexeme_start_p ) {
            offset_ls = me->_lexeme_start_p - FrontP; 
            __quex_assert(offset_ls < ContentSize); 
            move_distance = QUEX_MIN(move_distance, offset_ls);
        }

        move_size     = ContentSize - move_distance;

        __QUEX_STD_memmove((void*)&FrontP[move_distance], (void*)FrontP, 
                           move_size * sizeof(QUEX_TYPE_CHARACTER));

        me->_input_p += move_distance;
        if( me->_memory._end_of_file_p ) {
            me->_memory._end_of_file_p += move_distance;
        }
        if( me->_lexeme_start_p ) {
            me->_lexeme_start_p += move_distance;
        }

        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        QUEX_IF_ASSERTS_poison((void*)FrontP, (void*)&FrontP[move_distance]); 

        return move_distance;
    }

    QUEX_INLINE size_t          
    QUEX_NAME(BufferMemory_size)(QUEX_NAME(BufferMemory)* me)
    { return (size_t)(me->_back - me->_front + 1); }

    QUEX_INLINE void
    QUEX_NAME(Buffer_reverse_byte_order)(QUEX_TYPE_CHARACTER*       Begin, 
                                         const QUEX_TYPE_CHARACTER* End)
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
    QUEX_NAME(BufferMemory_construct)(QUEX_NAME(BufferMemory)*  me, 
                                      QUEX_TYPE_CHARACTER*      Memory, 
                                      const size_t              Size,
                                      E_Ownership               Ownership) 
    {
        __quex_assert(Memory);
        /* "Memory size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2" is reqired.
         * Maybe, define '-DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0' for 
         * compilation (assumed no pre-contexts.)                            */
        __quex_assert(Size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2);

        me->_front            = Memory;
        me->_back             = &Memory[Size-1];
        me->_end_of_file_p    = (QUEX_TYPE_CHARACTER*)0; /* LATER: Buffer_init_analyzis() */;
        me->ownership         = Ownership;
        *(me->_front)         = QUEX_SETTING_BUFFER_LIMIT_CODE;
        *(me->_back)          = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    QUEX_INLINE void 
    QUEX_NAME(BufferMemory_destruct)(QUEX_NAME(BufferMemory)* me) 
    /* Does not set 'me->_front' to zero, if it is not deleted. Thus, the user
     * may detect wether it needs to be deleted or not.                      */
    {
        if( me->_front && me->ownership == E_Ownership_LEXICAL_ANALYZER ) {
            QUEXED(MemoryManager_free)((void*)me->_front, 
                                       E_MemoryObjectType_BUFFER_MEMORY);
            /* Protect against double-destruction.                           */
            me->_front = me->_back = (QUEX_TYPE_CHARACTER*)0x0;
        }
    }

    QUEX_INLINE void  
    QUEX_NAME(Buffer_print_this)(QUEX_NAME(Buffer)* me)
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
        __QUEX_STD_printf("      _external_owner_f = %s;\n", me->_memory.ownership == E_Ownership_EXTERNAL ? "true" : "false");

        __QUEX_STD_printf("   _input_p        = +0x%X;\n", (int)(me->_input_p        - Offset));
        __QUEX_STD_printf("   _lexeme_start_p = +0x%X;\n", (int)(me->_lexeme_start_p - Offset));

        __QUEX_STD_printf("   _character_at_lexeme_start = %X;\n", (int)me->_character_at_lexeme_start);
#       ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        __QUEX_STD_printf("   _character_before_lexeme_start = %X;\n", (int)me->_character_before_lexeme_start);
#       endif
        __QUEX_STD_printf("   _content_character_index_begin = %i;\n", (int)QUEX_NAME(Buffer_character_index_begin)(me));
        __QUEX_STD_printf("   _content_character_index_end   = %i;\n", (int)me->_content_character_index_end);
        if( me->filler ) {
            __QUEX_STD_printf("   _byte_order_reversion_active_f = %s;\n", me->filler->_byte_order_reversion_active_f ? "true" : "false");
        }
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer_navigation.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I */


