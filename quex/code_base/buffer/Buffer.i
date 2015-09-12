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
        QUEX_TYPE_CHARACTER*      end_p;
        QUEX_TYPE_STREAM_POSITION end_character_index;

        __quex_assert( ! EndOfFileP || (EndOfFileP > me->_memory._front && EndOfFileP <= me->_memory._back));
        /* (1) BEFORE LOAD: The pointers must be defined which restrict the 
         *                  fill region. 
         *
         * The first state in the state machine does not increment. Thus, the
         * input pointer is set to the first position, not before.           */
        me->_read_p         = &me->_memory._front[1];  
        me->_lexeme_start_p = &me->_memory._front[1];  

        /* No character covered yet -> '\0'.                                 */
        me->_character_at_lexeme_start = '\0';  
#       ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
        me->_character_before_lexeme_start = QUEX_SETTING_CHARACTER_NEWLINE_IN_ENGINE_CODEC;  /* --> begin of line     */
#       endif

        /* (2) Load content, determine character indices of borders, determine
         *     end of file pointer.                                          */
        if( me->filler && me->filler->byte_loader ) {
            __quex_assert(! EndOfFileP);
            end_p               = (QUEX_TYPE_CHARACTER*)0;
            end_character_index = 0;
        } 
        else if( EndOfFileP ) {
            end_p               = EndOfFileP;
            end_character_index = EndOfFileP - &me->_memory._front[1];
        }
        else {
            end_p               = &me->_memory._front[1];
            end_character_index = 0;
        }
        QUEX_NAME(Buffer_input_end_set)(me, end_p, end_character_index);

        if( me->filler && me->filler->byte_loader ) {
            QUEX_NAME(BufferFiller_load_forward)(me);   
        }

        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_input_end_set)(QUEX_NAME(Buffer)*        me,
                                    QUEX_TYPE_CHARACTER*      EndOfInputP,
                                    QUEX_TYPE_STREAM_POSITION EndCharacterIndex)
    {
        __quex_assert(EndOfInputP > me->_memory._front);
        if( EndOfInputP > me->_memory._back ) {
            EndOfInputP = (QUEX_TYPE_CHARACTER*)0;
        }
        if( EndOfInputP ) {
            *EndOfInputP = QUEX_SETTING_BUFFER_LIMIT_CODE;
            if( EndOfInputP < me->_memory._back - 1 ) {
                QUEX_IF_ASSERTS_poison(&EndOfInputP[1], me->_memory._back);
            }
        }
        me->input.end_p               = EndOfInputP;
        me->input.end_character_index = EndCharacterIndex;
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_destruct)(QUEX_NAME(Buffer)* me)
    {
        QUEX_NAME(BufferFiller_delete)(&me->filler); 
        QUEX_NAME(BufferMemory_destruct)(&me->_memory);
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_read_p_add_offset)(QUEX_NAME(Buffer)* buffer, const size_t Offset)
    { 
        QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
        buffer->_read_p += Offset; 
        QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
    }

    QUEX_INLINE QUEX_TYPE_CHARACTER
    QUEX_NAME(Buffer_input_get_offset)(QUEX_NAME(Buffer)* me, const ptrdiff_t Offset)
    {
        QUEX_BUFFER_ASSERT_pointers_in_range(me);
        __quex_assert( me->_read_p + Offset > me->_memory._front );
        __quex_assert( me->_read_p + Offset <= me->_memory._back );
        return *(me->_read_p + Offset); 
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
        if( me->input.end_p ) return me->input.end_p;
        else                             return me->_memory._back;   
    }

    QUEX_INLINE ptrdiff_t
    QUEX_NAME(Buffer_distance_input_to_text_end)(QUEX_NAME(Buffer)* me)
    {
        QUEX_BUFFER_ASSERT_pointers_in_range(me);
        return QUEX_NAME(Buffer_text_end)(me) - me->_read_p;
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_end_of_file_set)(QUEX_NAME(Buffer)*   me, 
                                      QUEX_TYPE_CHARACTER* Position)
    {
        /* NOTE: The content starts at _front[1], since _front[0] contains 
         *       the buffer limit code. */
        me->input.end_p    = Position;
        *(me->input.end_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;

        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE void
    QUEX_NAME(Buffer_end_of_file_unset)(QUEX_NAME(Buffer)* buffer)
    {
        /* If the end of file pointer is to be 'unset' me must assume that the storage as been
         * overidden with something useful. Avoid setting input.end_p = 0x0 while the 
         * position pointed to still contains the buffer limit code.                             */
        buffer->input.end_p = 0x0;
        /* Not yet: QUEX_BUFFER_ASSERT_CONSISTENCY(me) -- pointers may still have to be adapted. */
    }

    QUEX_INLINE bool 
    QUEX_NAME(Buffer_is_end_of_file)(QUEX_NAME(Buffer)* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        return buffer->_read_p == buffer->input.end_p;
    }

    QUEX_INLINE bool                  
    QUEX_NAME(Buffer_is_begin_of_file)(QUEX_NAME(Buffer)* buffer)
    { 
        QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
        if     ( buffer->_read_p != buffer->_memory._front )           return false;
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
     *                         _read_p
     *                            |
     *            [case( x < 10 ) { print; } else ]
     *
     *   buffer after:   
     *              _read_p
     *                 |
     *            [case( x < 10 ) { print; } else ]
     *
     *            |----|
     *         fallback size                                                 */
    { 
        const QUEX_TYPE_CHARACTER*  FrontP        = &me->_memory._front[1];
        const QUEX_TYPE_CHARACTER*  BackP         = me->_memory._back;
        QUEX_TYPE_CHARACTER*        RemainderP    = me->_lexeme_start_p ? 
                                                      QUEX_MIN(me->_read_p, me->_lexeme_start_p)
                                                    : me->_read_p; 
        const QUEX_TYPE_CHARACTER*  RemainderEndP =   me->input.end_p ? 
                                                      me->input.end_p 
                                                    : me->_memory._back;
        QUEX_TYPE_CHARACTER*        end_p;
        QUEX_TYPE_STREAM_POSITION   end_character_index;
        QUEX_TYPE_CHARACTER*        move_begin_p;
        size_t                      move_size;
        ptrdiff_t                   move_distance;

        /* If distance to content front <= fallback size, no move possible.  */
        if( RemainderP < &FrontP[(ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N] ) {
            return (ptrdiff_t)0;
        }

        move_begin_p  = &RemainderP[- (ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N];
        move_size     = (ptrdiff_t)(RemainderEndP - move_begin_p);
        move_distance = move_begin_p - FrontP;

        /* Anything before '_read_p + 1' is considered to be 'past'. However,
         * leave a number of 'FALLBACK' to provide some pre-conditioning to
         * work.                                                             */
        __QUEX_STD_memmove((void*)FrontP, (void*)move_begin_p,
                           move_size * sizeof(QUEX_TYPE_CHARACTER));

        /* Adapt: _read_p, input.end_p, _lexeme_start_p, 
         *        input.end_character_index                               */
        me->_read_p -= move_distance;

        end_character_index = me->input.end_character_index - move_distance;
        end_p               = me->input.end_p ? me->input.end_p - move_distance
                                              : (QUEX_TYPE_CHARACTER*)0;
        QUEX_NAME(Buffer_input_end_set)(me, end_p, end_character_index);

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
        const QUEX_TYPE_STREAM_POSITION  CharacterIndexBegin = QUEX_NAME(Buffer_character_index_begin)(me);
        ptrdiff_t                        move_distance;
        ptrdiff_t                        move_size;
        ptrdiff_t                        offset_ls; 
        QUEX_TYPE_CHARACTER*             end_p;
        QUEX_TYPE_STREAM_POSITION        end_character_index;
   
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

        /* Adapt: _read_p, input.end_p, _lexeme_start_p, 
         *        input.end_character_index                                  */
        me->_read_p += move_distance;

        end_character_index = me->input.end_character_index + move_distance;
        end_p               = me->input.end_p ? me->input.end_p + move_distance
                                              : (QUEX_TYPE_CHARACTER*)0;
        QUEX_NAME(Buffer_input_end_set)(me, end_p, end_character_index);

        if( me->_lexeme_start_p ) {
            me->_lexeme_start_p += move_distance;
        }

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

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer_navigation.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I */


