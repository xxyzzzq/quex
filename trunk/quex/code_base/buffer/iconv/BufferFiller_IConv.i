// -*- C++ -*-  vim: set syntax=cpp:
// (C) 2007-2008 Frank-Rene Schaefer
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV_I_

#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/iconv/BufferFiller_IConv>

#include <quex/code_base/buffer/iconv/debug.i>


#if ! defined (__QUEX_SETTING_PLAIN_C)
    extern "C" { 
#   include <iconv.h>
    }
#   include <quex/code_base/compatibility/iconv-argument-types.h>

namespace quex {
#endif


    QuexBufferFiller_IConv_init(QUEX_CHARACTER_TYPE* input_handle, 
                                uint8_t*    raw_buffer_p, size_t      RawBufferSize,
                                const char* FromCoding,   const char* ToCoding) 
        /* Initialize the raw buffer that holds the plain bytes of the input file
         * (setup to trigger initial reload)                                                */
        : raw_buffer(raw_buffer_p, raw_buffer_size)
    { 
        ih = input_handle;

        /* Initialize the raw buffer that holds the plain bytes of the input file           */
        if( raw_buffer_p == 0x0 ) {
            raw_buffer_p = __QUEX_ALLOCATE_MEMORY(QUEX_CHARACTER_TYPE, RawBufferSize);
            me->_raw_buffer_external_owner_f = false;
        } else {
            me->_raw_buffer_external_owner_f = true;
        }
        QuexBufferFiller_IConv_BufferInfo_init(&raw_buffer, raw_buffer_p, RawBufferSize);

        me->raw_buffer.bytes_left_n  = 0;  /* --> trigger reload                            */

        /* Initialize the conversion operations                                             */
        me->iconv_handle = iconv_open(ToCoding, FromCoding);
        me->_constant_size_character_encoding_f = \
                        ! has_input_format_dynamic_character_width(FromCoding);

        /* Setup the tell/seek of character positions                                       */
        me->begin_info.position        = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
        me->begin_info.character_index = 0;
        me->end_info.position          = me->begin_info.position;
        me->end_info.character_index   = 0;

        QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_CONSTRUCTOR(FromCoding, ToCoding, me->iconv_handle);
    }

    TEMPLATE_IN(InputHandleT) void   
    __BufferFiller_IConv_destroy(QuexBufferFiller* alter_ego);
    { 
        if( ! me->_raw_buffer_external_owner_f ) __QUEX_FREE_MEMORY(me->raw_buffer);
        iconv_close(me->iconv_handle); 
    }

    TEMPLATE_IN(InputHandleT) size_t 
    __BufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                         QUEX_CHARACTER_TYPE* start_of_buffer, 
                                         const size_t         N);
    {
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;

        QuexBufferFiller_IConv_BufferInfo user_buffer;
        QuexBufferFiller_IConv_BufferInfo_init(&user_buffer, (uint8_t*)user_buffer_p, N * SizeOfCharacter);

        /* TWO CASES:
         * (1) There are still some bytes in the raw buffer from the last load.
         *     in this case, first translate them and then maybe load the raw buffer
         *     again. (raw_buffer.bytes_left_n != 0)
         * (2) The raw buffer is empty. Then it must be loaded in order to get some
         *     basis for conversion. (raw_buffer.bytes_left_n == 0)                      */
        if( me->raw_buffer.bytes_left_n == 0 ) __fill_raw_buffer(); 

        while( __convert(&user_buffer) == false ) { 
            QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_AND_USER_BUFFER(&user_buffer);
            __fill_raw_buffer(); 
        }
        QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_AND_USER_BUFFER(&user_buffer);

        if( user_buffer.bytes_left_n == 0 ) { 
            /* The buffer was filled to its limits. All 'N' characters have been written. */
            end_character_index += N;
            return N;
        } else { 
            /* The buffer was not filled completely, because the end of the file was 
             * reached. The fill level of the user buffer computes as:                    */
            const size_t ConvertedByteN = (user_buffer.size - user_buffer.bytes_left_n) / SizeOfCharacter;
            end_character_index += ConvertedByteN;
            return ConvertedByteN;
        }
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_fill_raw_buffer(TEMPLATED_CLASS(QuexBufferFiller_IConv)* me) 
    {
        // Try to fill the raw buffer to its limits with data from the file.
        // The filling starts from its current position, thus the remaining bytes
        // to be translated are exactly the number of bytes in the buffer.
        const size_t FillLevel       = me->raw_buffer.position - me->raw_buffer.begin;
        const size_t RemainingBytesN = me->raw_buffer.bytes_left_n;

        // There are cases (e.g. when a broken multibyte sequence occured at the end of 
        // the buffer) where there are bytes left in the raw buffer. These need to be
        // moved to the beginning of the buffer.
        if( me->raw_buffer.position != me->raw_buffer.begin ) {
            // Be careful: Maybe one can use 'memcpy()' which is a bit faster but the following
            // is safe against overlaps.
            std::memmove(me->raw_buffer.begin, me->raw_buffer.position, RemainingBytesN);
            // Reset the position, so that new conversion get's the whole character.
            me->raw_buffer.position = me->raw_buffer.begin; 
        }

        uint8_t*     FillStartPosition = me->raw_buffer.begin + me->raw_buffer.bytes_left_n;
        size_t       FillSize          = me->raw_buffer.size - me->raw_buffer.bytes_left_n;
        const size_t LoadedByteN = \
                     InputPolicy<QUEX_CHARACTER_TYPE*>::load_bytes(ih, FillStartPosition, FillSize);

        me->raw_buffer.bytes_left_n = LoadedByteN + RemainingBytesN; /* Bytes left for conversion in next run. */

        QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_BUFFER_LOAD(LoadedByteN);
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_fill_convert(TEMPLATED_CLASS(QuexBufferFiller_IConv)* me, 
                                          buffer_info*                             user_buffer) 
    {
        /* RETURNS:  true  --> User buffer is filled as much as possible with converted characters.
         *           false --> More raw bytes are needed to fill the user buffer.           
         *
         *  IF YOU GET AN ERROR HERE, THEN PLEASE HAVE A LOOK AT THE FILE:
         *
         *      quex/code_base/compatibility/iconv-argument-types.h
         * 
         *  The issue is, that 'iconv' is defined on different systems with different
         *  types of the second argument. There are two variants 'const char**'
         *  and 'char **'. If your system is not treated correctly, please
         *  contact the author <fschaef@users.sourceforge.net>.                             */
        size_t report = iconv(iconv_handle, 
                              (__Adapter_FuncIconv_SecondArgument)(&me->raw_buffer.position), &me->raw_buffer.bytes_left_n,
                              (char**)&(user_buffer->position),                               &(user_buffer->bytes_left_n));

        QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_ICONV_REPORT(report);

        if( report != (size_t)-1 ) { 
            /* (*) The input sequence (raw buffer content) has been converted completely.
             *     But, is the user buffer filled to its limits?                               */
            if( user_buffer->bytes_left_n == 0 ) return true; 
            /* If the buffer was not filled completely, then was it because we reached EOF?
             * NOTE: Here, 'raw_buffer.position' points to the position after the last byte
             *       that has been converted. If this is the end of the buffer, then it means
             *       that the raw buffer was read. If not, it means that the buffer has not been
             *       filled to its border which happens only if End of File occured.           */
            if( me->raw_buffer.position != me->raw_buffer.begin + me->raw_buffer.size ) {
                return true;
            }
            else {
                /* Else: The raw buffer needs more bytes. Since, everything went well, the new bytes
                 *       can be stored at the position '0' of the raw_buffer.                  */
                me->raw_buffer.position = me->raw_buffer.begin;
                /* please, refill ...                                                          */
                return false; 
            }
        }

        switch( errno ) {
        default:
            throw std::range_error("Unexpected setting of 'errno' after call to GNU's iconv().");

        case EILSEQ:
            throw std::range_error("Invalid byte sequence encountered for given character coding.");

        case EINVAL:
            /* (*) Incomplete byte sequence for character conversion
             *     ('raw_buffer.position' points to the beginning of the incomplete sequence.)
             *     Please, refill the buffer (consider copying the bytes from raw_buffer.position 
             *     to the end of the buffer in front of the new buffer).                             */
            return false; 

        case E2BIG:
            /* (*) The input buffer was not able to hold the number of converted characters.
             *     (in other words we're filled up to the limit and that's what we actually wanted.) */
            return true;
        }
    }


    TEMPLATE_IN(InputHandleT) size_t 
    __BufferFiller_IConv_tell_character_index(QuexBufferFiller* alter_ego);
    { 
        __quex_assert(alter_ego != 0x0); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type. */
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;
        return me->end_character_index; 
    }

    TEMPLATE_IN(InputHandleT) void   
    __BufferFiller_IConv_seek_character_index(QuexBufferFiller* alter_ego, 
                                              const size_t      CharacterIndex); 
    { 
        __quex_assert(alter_ego != 0x0); 
        /* The type cast is necessary, since the function signature needs to 
         * work with the first argument being of base class type.                          */
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;

        /* Seek_character_index(Pos) means that the next time when a character buffer
         * is to be filled, this has to happen from position 'CharacterIndex'. 
         *
         * NOTE: The reference for character positioning is **not** directly the stream.
         * Moreover, it is the internal raw_buffer.position. It determines what characters 
         * are converted next into the user's buffer.                                      
         *
         * Cases:
         *        (1) Anyway, the next character to be read == CharacterIndex
         *            => just relax, return without doing anything.
         *        (2) The coding has a constant character size (UCS-2, UCS-4, but not UTF-8)
         *            => seek according to computed stream position.
         *        (3) The CharacterIndex > character_index of the last stored
         *            pair of (character_index, stream position), then use that
         *            as a hint for the search of the stream position.
         *        (4) No hint, then start analysing from the beginning of the file.
         *            until the character index is reached (very worst case).
         */
        if( CharacterIndex == me->end_character_index ) { 
            return; 
        }
        else if( has_input_format_dynamic_character_width() ) { 
            long avoid_tmp_arg = (long)(CharacterIndex * sizeof(QUEX_CHARACTER_TYPE) + me->start_position); 
            QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, avoid_tmp_arg);
        } 
        else if( begin_info.character_index != 0 && CharacterIndex > begin_info.character_index ) {
            __QuexBufferFiller_IConv_seek_character_index_in_stream(me->begin_info.position, 
                                                                    me->begin_info.character_index, 
                                                                    CharacterIndex);
        } 
        else {
            __QuexBufferFiller_IConv_seek_character_index_in_stream(me->start_position, 0, CharacterIndex);
        } 
        /* Indicate: buffer reload required on next run! (trigger by bytes_left_n = 0) */
        me->raw_buffer.position     = me->raw_buffer.begin;
        me->raw_buffer.bytes_left_n = 0;
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_seek_character_index_in_stream(STREAM_POSITION_TYPE(InputHandleT) HintStreamPos, 
                                                            const size_t                       HintCharacterIndex,
                                                            const size_t CharacterIndex)
    { 
        const int            ChunkSize = 512;
        QUEX_CHARACTER_TYPE  chunk[512];
        /* This type of seek is not thought to be for cases where character positions
         * can be computed--as is the case for fixed character width encodings.       */
        __quex_assert(me->_constant_size_character_encoding_f == false);
        __quex_assert(HintCharacterIndex < CharacterIndex);            /* NOT: '<=' ! */

        /* STRATEGY: Starting from a certain point in the file we read characters
         *           (we convert them one by one) until we reach the given character
         *           index.                                                           */
        size_t  remaining_character_n = CharacterIndex - HintCharacterIndex;

        if( me->begin_info.position == HintStreamPos ) { 
            /* The 'read_characters()' function works on the content of the bytes
             * in the raw_buffer. The only thing that has to happen is to reset 
             * the raw buffer's position pointer to '0'.                              */
            me->raw_buffer.bytes_left_n += (me->raw_buffer.position - me->raw_buffer.begin);
            me->raw_buffer.position     = me->raw_buffer.begin;
        }
        else {
            /* We cannot make any assumptions about the relation between stream position
             * and character index--trigger reload (bytes_left_n = 0):                */
            me->raw_buffer.position     = me->raw_buffer.begin;
            me->raw_buffer.bytes_left_n = 0; 
            if ( me->end_info.position == HintStreamPos ) { 
                /* Here, no seek in the stream has to happen either, because the position
                 * points already to the right place.                                 */
                __quex_assert(me->end_info.character_index == HintCharacterIndex);
            } else { 
                QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, HintStreamPos);
            }
        }
        /* We are now at character index 'CharacterIndex - remaining_character_n' in the stream.
         * It remains to interpret 'remaining_character_n' number of characters. Since the
         * the interpretation is best done using a buffer, we do this in chunks.      */ 
        for(; remaining_character_n > ChunkSize; remaining_character_n -= ChunkSize )  
            read_characters(chunk, ChunkSize);
        if( remaining_character_n ) 
            read_characters(chunk, remaining_character_n);
       
        me->end_character_index = CharacterIndex;
    }

    TEMPLATE_IN(InputHandleT) void 
    __BufferFiller_IConv_mark_start_position(TEMPLATED_CLASS* me) 
    { 
       __quex_assert(me != 0x0); 
       me->start_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
    }

    TEMPLATE_IN(InputHandleT) void 
    __BufferFiller_IConv_reset_start_position(TEMPLATED_CLASS* me) 
    {
       __quex_assert(me != 0x0); 
        QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, me->start_position);
    }

    QUEX_INLINE_KEYWORD bool 
    CLASS::has_input_format_dynamic_character_width() 
    {
        return true; /* TODO: distinguish between different coding formats
        /*           //       'true' is safe, but possibly a little slower.  */
    }

    QUEX_INLINE_KEYWORD 
    QuexBufferFiller_IConv_BufferInfo_init(QuexBufferFiller_IConv_BufferInfo* me, 
                                           uint8_t* Begin, size_t SizeInBytes)
    {
        me->begin        = Begin;
        me->size         = SizeInBytes;
        me->position     = me->begin;
        me->bytes_left_n = me->size;
    }

#undef CLASS
#undef QUEX_INLINE_KEYWORD

}

#endif // __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV__
