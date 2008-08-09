// -*- C++ -*-  vim: set syntax=cpp:
// (C) 2007-2008 Frank-Rene Schaefer
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV_I_

#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/iconv/BufferFiller_IConv>
#include <quex/code_base/buffer/InputPolicy>

// #include <quex/code_base/buffer/iconv/debug.i>

#ifdef QUEX_OPTION_ASSERTS
#   define QUEX_ASSERT_BUFFER_INFO(BI)                                    \
    __quex_assert( BI != 0x0 );                                           \
    __quex_assert((*BI).position - (*BI).begin <= (*BI).size);            \
    __quex_assert((*BI).bytes_left_n <= (*BI).size); 
#else
#   define QUEX_ASSERT_BUFFER_INFO(BI) /* empty */
#endif


#ifndef __QUEX_SETTING_PLAIN_C
#   define TEMPLATED_CLASS                      QuexBufferFiller_IConv<InputHandleT>
#   define CHAR_INDEX_AND_STREAM_POSITION(TYPE) QuexCharacterIndexToStreamPosition<TYPE>
#else
#   define TEMPLATED_CLASS                      QuexBufferFiller_IConv
#   define CHAR_INDEX_AND_STREAM_POSITION(TYPE) QuexCharacterIndexToStreamPosition
#endif 

#if ! defined (__QUEX_SETTING_PLAIN_C)
    extern "C" { 
#   include <iconv.h>
    }
#   include <quex/code_base/compatibility/iconv-argument-types.h>
#endif

#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif
    QUEX_INLINE_KEYWORD bool 
    QuexBufferFiller_IConv_has_coding_dynamic_character_width(const char* Coding);

    QUEX_INLINE_KEYWORD void
    QuexBufferFiller_IConv_BufferInfo_init(QuexBufferFiller_IConv_BufferInfo* me, 
                                           uint8_t* Begin, size_t SizeInBytes);

    TEMPLATE_IN(InputHandleT) size_t 
    __QuexBufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                             QUEX_CHARACTER_TYPE* user_memory_p, 
                                             const size_t         N);

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_fill_raw_buffer(TEMPLATED_CLASS*);

    TEMPLATE_IN(InputHandleT) bool 
    __QuexBufferFiller_IConv_convert(TEMPLATED_CLASS*                   me, 
                                     QuexBufferFiller_IConv_BufferInfo* drain);

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_seek_character_index_in_stream(TEMPLATED_CLASS* me,
                                                            STREAM_POSITION_TYPE(InputHandleT) HintStreamPos, 
                                                            const size_t                       HintCharacterIndex,
                                                            const size_t CharacterIndex);

    TEMPLATE_IN(InputHandleT) void
    QuexBufferFiller_IConv_init(TEMPLATED_CLASS* me,
                                InputHandleT* input_handle, 
                                const char* FromCoding,   const char* ToCoding,
                                uint8_t*    raw_buffer_p, size_t      RawBufferSize)
    { 
        __quex_assert(RawBufferSize >= 6); /* UTF-8 char can be 6 bytes long */
#       if ! defined(__QUEX_SETTING_PLAIN_C)
        __QuexBufferFiller_init(&me->base,
                                __QuexBufferFiller_IConv_tell_character_index<InputHandleT>,
                                __QuexBufferFiller_IConv_seek_character_index<InputHandleT>, 
                                __QuexBufferFiller_IConv_read_characters<InputHandleT>,
                                __QuexBufferFiller_IConv_destroy<InputHandleT>);
#       else 
        __QuexBufferFiller_init(&me->base,
                                __QuexBufferFiller_IConv_tell_character_index,
                                __QuexBufferFiller_IConv_seek_character_index, 
                                __QuexBufferFiller_IConv_read_characters,
                                __QuexBufferFiller_IConv_destroy);
#       endif

        /* Initialize the raw buffer that holds the plain bytes of the input file
         * (setup to trigger initial reload)                                                */
        me->ih = input_handle;

        /* Initialize the raw buffer that holds the plain bytes of the input file           */
        if( raw_buffer_p == 0x0 ) {
            raw_buffer_p = __QUEX_ALLOCATE_MEMORY(uint8_t, RawBufferSize);
            me->_raw_buffer_external_owner_f = false;
        } else {
            me->_raw_buffer_external_owner_f = true;
        }
        QuexBufferFiller_IConv_BufferInfo_init(&me->raw_buffer, raw_buffer_p, RawBufferSize);

        me->raw_buffer.bytes_left_n  = 0;  /* --> trigger reload                            */

        /* Initialize the conversion operations                                             */
        me->iconv_handle = iconv_open(ToCoding, FromCoding);
        me->_constant_size_character_encoding_f = \
                        ! QuexBufferFiller_IConv_has_coding_dynamic_character_width(FromCoding);

        /* Setup the tell/seek of character positions                                       */
        me->begin_info.position        = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
        me->begin_info.character_index = 0;
        me->end_info.position          = me->begin_info.position;
        me->end_info.character_index   = 0;

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_CONSTRUCTOR(FromCoding, ToCoding, me->iconv_handle);*/
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    TEMPLATE_IN(InputHandleT) void   
    __QuexBufferFiller_IConv_destroy(QuexBufferFiller* alter_ego)
    { 
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
        if( ! me->_raw_buffer_external_owner_f ) __QUEX_FREE_MEMORY(&me->raw_buffer);
        iconv_close(me->iconv_handle); 
    }

    TEMPLATE_IN(InputHandleT) size_t 
    __QuexBufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                             QUEX_CHARACTER_TYPE* user_memory_p, 
                                             const size_t         N)
    {
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;

        QuexBufferFiller_IConv_BufferInfo user_buffer;
        QuexBufferFiller_IConv_BufferInfo_init(&user_buffer, (uint8_t*)user_memory_p, 
                                               N * sizeof(QUEX_CHARACTER_TYPE));
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
        QUEX_ASSERT_BUFFER_INFO(&user_buffer);

        /* TWO CASES:
         * (1) There are still some bytes in the raw buffer from the last load.
         *     in this case, first translate them and then maybe load the raw buffer
         *     again. (raw_buffer.bytes_left_n != 0)
         * (2) The raw buffer is empty. Then it must be loaded in order to get some
         *     basis for conversion. (raw_buffer.bytes_left_n == 0)                      */
        if( me->raw_buffer.bytes_left_n == 0 ) __QuexBufferFiller_IConv_fill_raw_buffer(me); 

        while( __QuexBufferFiller_IConv_convert(me, &user_buffer) == false ) { 
            /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_AND_USER_BUFFER(&user_buffer);*/
            __QuexBufferFiller_IConv_fill_raw_buffer(me); 
        }
        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_AND_USER_BUFFER(&user_buffer);*/

        if( user_buffer.bytes_left_n == 0 ) { 
            /* The buffer was filled to its limits. All 'N' characters have been written. */
            me->end_info.character_index += N;
            return N;
        } else { 
            /* The buffer was not filled completely, because the end of the file was 
             * reached. The fill level of the user buffer computes as:                    */
            const size_t ConvertedByteN = (user_buffer.size - user_buffer.bytes_left_n) / sizeof(QUEX_CHARACTER_TYPE);
            me->end_info.character_index += ConvertedByteN;
            return ConvertedByteN;
        }
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_fill_raw_buffer(TEMPLATED_CLASS*  me) 
    {
        /* Try to fill the raw buffer to its limits with data from the file.
         * The filling starts from its current position, thus the remaining bytes
         * to be translated are exactly the number of bytes in the buffer.              */
        QuexBufferFiller_IConv_BufferInfo* buffer = &me->raw_buffer;
        const size_t FillLevel       = buffer->position - buffer->begin;
        const size_t RemainingBytesN = buffer->bytes_left_n;
        QUEX_ASSERT_BUFFER_INFO(buffer);

        /* There are cases (e.g. when a broken multibyte sequence occured at the end of 
         * the buffer) where there are bytes left in the raw buffer. These need to be
         * moved to the beginning of the buffer.                                        */
        if( buffer->position != buffer->begin ) {
            /* Be careful: Maybe one can use 'memcpy()' which is a bit faster but the
             * following is safe against overlaps.                                      */
            std::memmove(buffer->begin, buffer->position, RemainingBytesN);
            /* Reset the position, so that new conversion get's the whole character.    */
            buffer->position = buffer->begin; 
        }

        uint8_t*     FillStartPosition = buffer->begin + RemainingBytesN;
        size_t       FillSize          = buffer->size  - RemainingBytesN;
        const size_t LoadedByteN = \
                     QUEX_INPUT_POLICY_LOAD_BYTES(me->ih, InputHandleT, FillStartPosition, FillSize);

        /* NOTE: In case of 'end of file' it is possible: bytes_left_n != buffer->size */
        buffer->bytes_left_n = LoadedByteN + RemainingBytesN; 

#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset(buffer->begin + buffer->bytes_left_n, 0xFF, 
                          buffer->size  - buffer->bytes_left_n);
#       endif

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_BUFFER_LOAD(LoadedByteN);*/
        QUEX_ASSERT_BUFFER_INFO(buffer);
    }

    TEMPLATE_IN(InputHandleT) bool 
    __QuexBufferFiller_IConv_convert(TEMPLATED_CLASS*                   me, 
                                     QuexBufferFiller_IConv_BufferInfo* drain) 
    {
        /* RETURNS:  true  --> User buffer is filled as much as possible with converted 
         *                     characters.
         *           false --> More raw bytes are needed to fill the user buffer.           
         *
         *  IF YOU GET A COMPILE ERROR HERE, THEN PLEASE HAVE A LOOK AT THE FILE:
         *
         *      quex/code_base/compatibility/iconv-argument-types.h
         * 
         *  The issue is, that 'iconv' is defined on different systems with different
         *  types of the second argument. There are two variants 'const char**'
         *  and 'char **'.  If you get an error here, consider defining 
         *
         *            -DQUEX_SETTING_ICONV_2ND_ARG_CONST_CHARPP
         *
         *  as a compile option. If you have an elegant solution to solve the problem for 
         *  plain 'C', then please, let me know <fschaef@users.sourceforge.net>.               */
        QuexBufferFiller_IConv_BufferInfo* source = &me->raw_buffer;
        QUEX_ASSERT_BUFFER_INFO(source);
        QUEX_ASSERT_BUFFER_INFO(drain);
        size_t report = iconv(me->iconv_handle, 
                              __QUEX_ADAPTER_ICONV_2ND_ARG(&source->position), &source->bytes_left_n,
                              (char**)&(drain->position),                      &(drain->bytes_left_n));

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_ICONV_REPORT(report);*/

        if( report != (size_t)-1 ) { 
            /* The input sequence (raw buffer content) has been converted completely.
             * But, is the user buffer filled to its limits?                                   */
            if( drain->bytes_left_n == 0 ) return true; 
            /* If the buffer was not filled completely, then was it because we reached EOF?
             * NOTE: Here, 'source->position' points to the position after the last byte
             *       that has been converted. If this is the end of the buffer, then it means
             *       that the raw buffer was read. If not, it means that the buffer has not been
             *       filled to its border which happens only if End of File occured.           */
            if( source->position != source->begin + source->size ) {
                return true;
            }
            else {
                /* Else: The raw buffer needs more bytes. Since, everything went well, the new bytes
                 *       can be stored at the position '0' of the raw_buffer.                  */
                source->position = source->begin;
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
    __QuexBufferFiller_IConv_tell_character_index(QuexBufferFiller* alter_ego)
    { 
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED_CLASS* me = (TEMPLATED_CLASS*)alter_ego;
        return me->end_info.character_index; 
    }

    TEMPLATE_IN(InputHandleT) void   
    __QuexBufferFiller_IConv_seek_character_index(QuexBufferFiller* alter_ego, 
                                              const size_t      CharacterIndex)
    { 
        __quex_assert(alter_ego != 0x0); 
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
        if( CharacterIndex == me->end_info.character_index ) { 
            return; 
        }
        else if( me->_constant_size_character_encoding_f ) { 
            long avoid_tmp_arg = (long)(CharacterIndex * sizeof(QUEX_CHARACTER_TYPE) + me->start_position); 
            QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, avoid_tmp_arg);
        } 
        else if( me->begin_info.character_index != 0 && CharacterIndex > me->begin_info.character_index ) {
            __QuexBufferFiller_IConv_seek_character_index_in_stream(me, me->begin_info.position, 
                                                                    me->begin_info.character_index, 
                                                                    CharacterIndex);
        } 
        else {
            __QuexBufferFiller_IConv_seek_character_index_in_stream(me, me->start_position, 0, CharacterIndex);
        } 
        /* Indicate: buffer reload required on next run! (trigger by bytes_left_n = 0) */
        me->raw_buffer.position     = me->raw_buffer.begin;
        me->raw_buffer.bytes_left_n = 0;
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_seek_character_index_in_stream(TEMPLATED_CLASS* me,
                                                            STREAM_POSITION_TYPE(InputHandleT) HintStreamPos, 
                                                            const size_t                       HintCharacterIndex,
                                                            const size_t CharacterIndex)
    { 
        const size_t         ChunkSize = 512;
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
            me->base.read_characters(&me->base, (QUEX_CHARACTER_TYPE*)chunk, ChunkSize);
        if( remaining_character_n ) 
            me->base.read_characters(&me->base, (QUEX_CHARACTER_TYPE*)chunk, remaining_character_n);
       
        me->end_info.character_index = CharacterIndex;
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_mark_start_position(TEMPLATED_CLASS* me) 
    { 
       __quex_assert(me != 0x0); 
       me->start_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
    }

    TEMPLATE_IN(InputHandleT) void 
    __QuexBufferFiller_IConv_reset_start_position(TEMPLATED_CLASS* me) 
    {
       __quex_assert(me != 0x0); 
        QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, me->start_position);
    }

    QUEX_INLINE_KEYWORD bool 
    QuexBufferFiller_IConv_has_coding_dynamic_character_width(const char* Coding) 
    {
        return true; /* TODO: distinguish between different coding formats
        /*           //       'true' is safe, but possibly a little slower.  */
    }

    QUEX_INLINE_KEYWORD void
    QuexBufferFiller_IConv_BufferInfo_init(QuexBufferFiller_IConv_BufferInfo* me, 
                                           uint8_t* Begin, size_t SizeInBytes)
    {
        me->begin        = Begin;
        me->size         = SizeInBytes;
        me->position     = me->begin;
        me->bytes_left_n = me->size;

#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset(Begin, 0xFF, SizeInBytes);
#       endif
    }

#undef CLASS
#undef QUEX_INLINE_KEYWORD
#undef CHAR_INDEX_AND_STREAM_POSITION
}

#include <quex/code_base/temporary_macros_off>

#endif // __INCLUDE_GUARD__QUEX_BUFFER_INPUT_STRATEGY_ICONV__
