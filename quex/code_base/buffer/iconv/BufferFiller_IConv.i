/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__
#define __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__

#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/iconv/BufferFiller_IConv>
#include <quex/code_base/buffer/InputPolicy>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/compatibility/iconv-argument-types.h>

#ifdef QUEX_OPTION_ASSERTS
#   define QUEX_ASSERT_BUFFER_INFO(BI)                         \
    __quex_assert( BI != 0x0 );                                \
    __quex_assert((BI)->iterator >= (BI)->begin);              \
    __quex_assert((BI)->iterator <= (BI)->end);                \
    __quex_assert((BI)->end >= (BI)->begin);                   \
    __quex_assert((BI)->end <= (BI)->memory_end);             

#   define QUEX_ASSERT_BUFFER_INFO_EASY(BI)                    \
    __quex_assert( BI != 0x0 );                                \
    __quex_assert((BI)->iterator >= (BI)->begin);              \
    __quex_assert((BI)->iterator <= (BI)->end);                     

#else
#   define QUEX_ASSERT_BUFFER_INFO(BI)      /* empty */
#   define QUEX_ASSERT_BUFFER_INFO_EASY(BI) /* empty */
#endif

#if ! defined (__QUEX_SETTING_PLAIN_C)
#   include <quex/code_base/compatibility/iconv-argument-types.h>
#   include <cerrno>
#else
#   include <errno.h>
#endif

#include <quex/code_base/temporary_macros_on>

#if ! defined (__QUEX_SETTING_PLAIN_C)
namespace quex {
#endif
    TEMPLATE_IN(InputHandleT) size_t __QuexBufferFiller_IConv_tell_character_index(QuexBufferFiller* alter_ego);
    TEMPLATE_IN(InputHandleT) void   __QuexBufferFiller_IConv_seek_character_index(QuexBufferFiller* alter_ego, 
                                                                                   const size_t      CharacterIndex); 
    TEMPLATE_IN(InputHandleT) size_t __QuexBufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                                                              QUEX_CHARACTER_TYPE* start_of_buffer, 
                                                                              const size_t         N);
    TEMPLATE_IN(InputHandleT) void   __QuexBufferFiller_IConv_destroy(QuexBufferFiller* alter_ego);

    TEMPLATE_IN(InputHandleT) size_t __QuexBufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                                                              QUEX_CHARACTER_TYPE* user_memory_p, 
                                                                              const size_t         N);

    TEMPLATE_IN(InputHandleT) size_t __QuexBufferFiller_IConv_fill_raw_buffer(TEMPLATED(QuexBufferFiller_IConv)*);

    TEMPLATE_IN(InputHandleT) bool   __QuexBufferFiller_IConv_convert(TEMPLATED(QuexBufferFiller_IConv)*   me, 
                                                                      uint8_t**                   source, 
                                                                      const uint8_t*              SourceEnd,
                                                                      QUEX_CHARACTER_TYPE**       drain,  
                                                                      const QUEX_CHARACTER_TYPE*  DrainEnd);

    QUEX_INLINE bool QuexBufferFiller_IConv_has_coding_dynamic_character_width(const char* Coding);

    TEMPLATE_IN(InputHandleT) void   QuexBufferFiller_IConv_BufferInfo_init(
                                           TEMPLATED(QuexBufferFiller_IConv_BufferInfo)* me, 
                                           uint8_t* Begin, size_t SizeInBytes,
                                           STREAM_POSITION_TYPE(InputHandleT) StartPosition);

    TEMPLATE_IN(InputHandleT) void QuexBufferFiller_IConv_hint_set(CHAR_INDEX_AND_STREAM_POSITION(InputHandleT)*  me, 
                                                     size_t                                 CharacterIndex, 
                                                     ptrdiff_t                              Offset, 
                                                     STREAM_POSITION_TYPE(InputHandleT)     StreamPosition);

    /******/
    /* QUEX_INLINE void */
    TEMPLATE_IN(InputHandleT) void
    QuexConverter_IConv_open(TEMPLATED(QuexBufferFiller_IConv)* me,
                             const char* FromCoding, const char* ToCoding)
    {
        /* QuexConverter_IConv* me = (QuexConverter_IConv*)alter_ego; */
        __quex_assert(me != 0x0);

        const char* to_coding = ToCoding != 0x0 ? ToCoding : QUEX_SETTING_CORE_ENGINE_DEFAULT_CHARACTER_CODING;

        me->iconv_handle = iconv_open(to_coding, FromCoding);
        if( me->iconv_handle == (iconv_t)-1 ) {
            char tmp[128];
            snprintf(tmp, 127, "Conversion '%s' --> '%s' is not supported by 'iconv'.\n", FromCoding, to_coding);
            QUEX_ERROR_EXIT(tmp);
        }
    }
    /******/

    TEMPLATE_IN(InputHandleT) void
    QuexBufferFiller_IConv_construct(TEMPLATED(QuexBufferFiller_IConv)* me,
                                     InputHandleT* input_handle, 
                                     const char*   FromCoding,   const char* ToCoding,
                                     size_t        RawBufferSize)
    { 
        const char* to_coding = ToCoding != 0x0 ? ToCoding : QUEX_SETTING_CORE_ENGINE_DEFAULT_CHARACTER_CODING;

        __quex_assert(RawBufferSize >= 6);  /* UTF-8 char can be 6 bytes long    */

        __QuexBufferFiller_init_functions(&me->base,
                                          TEMPLATED(__QuexBufferFiller_IConv_tell_character_index),
                                          TEMPLATED(__QuexBufferFiller_IConv_seek_character_index), 
                                          TEMPLATED(__QuexBufferFiller_IConv_read_characters),
                                          TEMPLATED(__QuexBufferFiller_IConv_destroy));

        /* Initialize the raw buffer that holds the plain bytes of the input file
         * (setup to trigger initial reload)                                                */
        me->ih = input_handle;

        /* Initialize the conversion operations                                             */
        QuexConverter_IConv_open(me, FromCoding, to_coding);

        me->_constant_size_character_encoding_f = \
                        ! QuexBufferFiller_IConv_has_coding_dynamic_character_width(FromCoding);

        /* Setup the tell/seek of character positions                                       */
        me->start_position      = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);

        /* Initialize the raw buffer that holds the plain bytes of the input file           */
        uint8_t* raw_buffer_p = MemoryManager_get_BufferFiller_RawBuffer(RawBufferSize);
        QuexBufferFiller_IConv_BufferInfo_init(&me->raw_buffer, raw_buffer_p, RawBufferSize, 
                                               me->start_position);

        /* Hint for relation between character index, raw buffer offset and stream position */
        QuexBufferFiller_IConv_hint_set(&me->hint_0, 0, 0, me->start_position);

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_CONSTRUCTOR(FromCoding, ToCoding, me->iconv_handle);*/
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    TEMPLATE_IN(InputHandleT) void   
    __QuexBufferFiller_IConv_destroy(QuexBufferFiller* alter_ego)
    { 
        TEMPLATED(QuexBufferFiller_IConv)* me = (TEMPLATED(QuexBufferFiller_IConv)*)alter_ego;
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);

        iconv_close(me->iconv_handle); 

        MemoryManager_free_BufferFiller_RawBuffer(me->raw_buffer.begin); 

        /* The memory manager allocated the space required for a buffer filler of this
         * type. Somewhere down the road it is known what size of memory belongs to this
         * pointer. */
        MemoryManager_free_BufferFiller(alter_ego);
    }

    TEMPLATE_IN(InputHandleT) size_t 
    __QuexBufferFiller_IConv_read_characters(QuexBufferFiller*    alter_ego,
                                             QUEX_CHARACTER_TYPE* user_memory_p, 
                                             const size_t         N)
    {
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED(QuexBufferFiller_IConv)* me = (TEMPLATED(QuexBufferFiller_IConv)*)alter_ego;

        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);

        /* TWO CASES:
         * (1) There are still some bytes in the raw buffer from the last load.
         *     in this case, first translate them and then maybe load the raw buffer
         *     again. (iterator != end)
         * (2) The raw buffer is empty. Then it must be loaded in order to get some
         *     basis for conversion. (iterator == end)                                */
        if( me->raw_buffer.iterator == me->raw_buffer.end ) 
            /* If no bytes can be loaded, then zero characters are converted */
            if( __QuexBufferFiller_IConv_fill_raw_buffer(me) == 0 ) { return 0; }

        QUEX_CHARACTER_TYPE*        user_buffer_iterator = user_memory_p;
        const QUEX_CHARACTER_TYPE*  UserBufferEnd        = user_memory_p + N;
        while( ! __QuexBufferFiller_IConv_convert(me, 
                                                  &me->raw_buffer.iterator, 
                                                  me->raw_buffer.end,
                                                  &user_buffer_iterator, 
                                                  UserBufferEnd) ) {

            __quex_assert(me->raw_buffer.iterator <= me->raw_buffer.end);

            if( __QuexBufferFiller_IConv_fill_raw_buffer(me) == 0 ) {
                /* No bytes have been loaded. */
                if( me->raw_buffer.end != me->raw_buffer.begin ) 
                    /* There are still bytes, but they were not converted by the converter. */
                    QUEX_ERROR_EXIT("Error. At end of file, byte sequence not interpreted as character.");
                break;
            }
        }

        const size_t ConvertedCharN = (size_t)(user_buffer_iterator - user_memory_p);
        me->raw_buffer.iterators_character_index += ConvertedCharN;

        if( ConvertedCharN != N ) {
            /* The buffer was not filled completely, because the end of the file was reached.   */
#           ifdef QUEX_OPTION_ASSERTS
            /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
            __QUEX_STD_memset((uint8_t*)(user_buffer_iterator), (uint8_t)0xFF, 
                              (UserBufferEnd - user_buffer_iterator) * sizeof(QUEX_CHARACTER_TYPE));
#           endif
        }
        return ConvertedCharN;
    }

    TEMPLATE_IN(InputHandleT) size_t 
    __QuexBufferFiller_IConv_fill_raw_buffer(TEMPLATED(QuexBufferFiller_IConv)*  me) 
    {
        /* Try to fill the raw buffer to its limits with data from the file.
         * The filling starts from its current position, thus the remaining bytes
         * to be translated are exactly the number of bytes in the buffer.              */
        TEMPLATED(QuexBufferFiller_IConv_BufferInfo)*  buffer          = &me->raw_buffer;
        const size_t                                   RemainingBytesN = buffer->end - buffer->iterator;
        QUEX_ASSERT_BUFFER_INFO(buffer);
        __quex_assert((size_t)(buffer->end - buffer->begin) >= RemainingBytesN);
        __quex_assert(buffer->end_stream_position == QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT));

        /* Store information about the current iterators character index. */
        QuexBufferFiller_IConv_hint_set(&me->hint_0, 
                                        buffer->iterators_character_index,
                                        RemainingBytesN,
                                        buffer->end_stream_position);

        /* There are cases (e.g. when a broken multibyte sequence occured at the end of 
         * the buffer) where there are bytes left in the raw buffer. These need to be
         * moved to the beginning of the buffer.                                        */
        if( RemainingBytesN != 0 ) {
            /* Be careful: Maybe one can use 'memcpy()' which is a bit faster but the
             * following is safe against overlaps.                                      */
            /* Cast to uint8_t to avoid a spurious function overload */
            __QUEX_STD_memmove((uint8_t*)(buffer->begin), (uint8_t*)(buffer->iterator), RemainingBytesN);
        }

        uint8_t*     FillStartPosition = buffer->begin + RemainingBytesN;
        size_t       FillSize          = (buffer->memory_end - buffer->begin) - RemainingBytesN;
        const size_t LoadedByteN = \
                     QUEX_INPUT_POLICY_LOAD_BYTES(me->ih, InputHandleT, FillStartPosition, FillSize);

        buffer->end = buffer->begin + LoadedByteN + RemainingBytesN;

        buffer->end_stream_position = QUEX_INPUT_POLICY_TELL(me->ih, InputHandleT);
        /* '.character_index' remains to be updated after character conversion */

        /* In any case, we start reading from the beginning of the raw buffer. */
        buffer->iterator = buffer->begin; 

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_BUFFER_LOAD(LoadedByteN);*/
        QUEX_ASSERT_BUFFER_INFO(buffer);

        return LoadedByteN;
    }

    TEMPLATE_IN(InputHandleT) bool 
    __QuexBufferFiller_IConv_convert(TEMPLATED(QuexBufferFiller_IConv)*   me, 
                                     uint8_t**              source, const uint8_t*              SourceEnd,
                                     QUEX_CHARACTER_TYPE**  drain,  const QUEX_CHARACTER_TYPE*  DrainEnd)
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
        size_t source_bytes_left_n = SourceEnd - *source;
        size_t drain_bytes_left_n  = (DrainEnd - *drain)*sizeof(QUEX_CHARACTER_TYPE);

        size_t report = iconv(me->iconv_handle, 
                              __QUEX_ADAPTER_ICONV_2ND_ARG(source), &source_bytes_left_n,
                              (char**)drain,                        &drain_bytes_left_n);

        if( report != (size_t)-1 ) { 
            __quex_assert(source_bytes_left_n == 0);
            /* The input sequence (raw buffer content) has been converted completely.
             * But, is the user buffer filled to its limits?                                   */
            if( drain_bytes_left_n == 0 ) {
                __quex_assert(*drain == DrainEnd);
                return true; 
            }
            /* If the buffer was not filled completely, then was it because we reached EOF?
             * NOTE: Here, 'source->iterator' points to the position after the last byte
             *       that has been converted. If this is the end of the buffer, then it means
             *       that the raw buffer was read. If not, it means that the buffer has not been
             *       filled to its border which happens only if End of File occured.           */
            if( *source != SourceEnd ) {
                /*__quex_assert(me->raw_buffer.end != me->raw_buffer.memory_end);*/
                return true;
            }
            else {
                /* Else: The user buffer is still hungry, thus the raw buffer needs more bytes. */
                /* *source == SourceEnd anyway, so 'refill' is triggered at any time.           */
                return false; 
            }
        }

        switch( errno ) {
        default:
            QUEX_ERROR_EXIT("Unexpected setting of 'errno' after call to GNU's iconv().");

        case EILSEQ:
            QUEX_ERROR_EXIT("Invalid byte sequence encountered for given character coding.");

        case EINVAL:
            /* Incomplete byte sequence for character conversion
             * ('raw_buffer.iterator' points to the beginning of the incomplete sequence.)
             * Please, refill the buffer (consider copying the bytes from raw_buffer.iterator 
             * to the end of the buffer in front of the new buffer).                             */
            return false; 

        case E2BIG:
            /* The input buffer was not able to hold the number of converted characters.
             * (in other words we're filled up to the limit and that's what we actually wanted.) */
            return true;
        }
    }


    TEMPLATE_IN(InputHandleT) size_t 
    __QuexBufferFiller_IConv_tell_character_index(QuexBufferFiller* alter_ego)
    { 
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED(QuexBufferFiller_IConv)* me = (TEMPLATED(QuexBufferFiller_IConv)*)alter_ego;
        /* The raw buffer iterator stands on the next character to be read. In general it holds
         * that the raw_buffer's iterator points to the first byte of the next character to be
         * converted when the next user buffer is to be filled.                                      */
        return me->raw_buffer.iterators_character_index; 
    }

    TEMPLATE_IN(InputHandleT) void   
    __QuexBufferFiller_IConv_seek_character_index(QuexBufferFiller*  alter_ego, 
                                                  const size_t       Index)
    { 
        /* The goal of the 'seek' is that the next filling of the user buffer starts at 
         * the specified character index 'Index'. This can be achieved by setting the 
         * raw buffer iterator.       
         *                                                                                        */
        /* NOTE: This differs from QuexBuffer_seek(...) in the sense, that it only sets the
         *       stream to a particular position given by a character index. QuexBuffer_seek(..)
         *       sets the _input_p to a particular position.                                      */
        __quex_assert(alter_ego != 0x0); 
        TEMPLATED(QuexBufferFiller_IConv)*             me          = (TEMPLATED(QuexBufferFiller_IConv)*)alter_ego;
        TEMPLATED(QuexBufferFiller_IConv_BufferInfo)*  buffer      = &me->raw_buffer;
        const size_t                                   Hint0_Index = me->hint_0.character_index;

        /* Seek_character_index(Pos) means that the next time when a character buffer
         * is to be filled, this has to happen from position 'CharacterIndex'. 
         *
         * NOTE: The reference for character positioning is **not** directly the stream.
         * Moreover, it is the internal raw_buffer.position. It determines what characters 
         * are converted next into the user's buffer.                                             */
        if( Index == buffer->iterators_character_index ) { 
            return;                                                /* Nothing to be done          */
        }
        /* Depending on the character encoding, the seek procedure can be optimized there are the 
         * following two cases:
         *
         *   (1) The coding uses **fixed** character widths (such as ASCII, UCS2, UCS4, etc.) where
         *       each character always occupies the same amount of bytes. Here, offsets can be 
         *       **computed**. This makes things faster.
         *   (2) The coding uses **dynamic** character width (e.g. UTF-8). Here the position cannot
         *       be computed. Instead, the conversion must start from a given 'known' position 
         *       until one reaches the specified character index.                                 */
        if( me->_constant_size_character_encoding_f ) { 
            /* (1) Fixed Character Width */
            const size_t ContentSize = buffer->end - buffer->begin;
            const size_t EndIndex    = Hint0_Index + (ContentSize / sizeof(QUEX_CHARACTER_TYPE));
            if( Index >= Hint0_Index && Index < EndIndex ) {
                uint8_t* new_iterator  = buffer->begin + (Index - Hint0_Index) * sizeof(QUEX_CHARACTER_TYPE);
                buffer->iterator                  = new_iterator;
                buffer->iterators_character_index = Index;
            }
            else  /* Index not in [BeginIndex:EndIndex) */ {
                STREAM_POSITION_TYPE(InputHandleT) avoid_tmp_arg =
                    (STREAM_POSITION_TYPE(InputHandleT))(Index * sizeof(QUEX_CHARACTER_TYPE) + me->start_position);
                QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, avoid_tmp_arg);
                buffer->end_stream_position = avoid_tmp_arg;
                /* iterator == end => trigger reload                                              */
                buffer->iterator                  = buffer->end;
                buffer->iterators_character_index = Index;
            }
        } 
        else  { 
            /* (2) Dynamic Character Width */
            /* Setting the iterator to the begin of the raw_buffer initiates a conversion
             * start from this point.                                                             */
            if( Index == Hint0_Index ) { 
                /* The 'read_characters()' function works on the content of the bytes
                 * in the raw_buffer. The only thing that has to happen is to reset 
                 * the raw buffer's position pointer to '0'.                                      */
                buffer->iterators_character_index = Index;
                buffer->iterator                  = buffer->begin + me->hint_0.offset;
            }
            else if( Index > Hint0_Index ) { 
                /* The searched index lies in the current raw_buffer or behind. Simply start 
                 * conversion from the current position until it is reached--but use the stuff 
                 * currently inside the buffer.                                                   */
                buffer->iterators_character_index = Hint0_Index;
                buffer->iterator                  = buffer->begin + me->hint_0.offset;
                __QuexBufferFiller_step_forward_n_characters((QuexBufferFiller*)me, Index - Hint0_Index);
                /* assert on index position, see end of 'step_forward_n_characters(...)'.         */
            }
            else  /* Index < BeginIndex */ {
                /* No idea where to start --> start from the beginning. In some cases this might
                 * mean a huge performance penalty. But note, that this only occurs at pre-conditions
                 * that are very very long and happen right at the beginning of the raw buffer.   */
                QUEX_INPUT_POLICY_SEEK(me->ih, InputHandleT, me->start_position);
                buffer->end_stream_position = me->start_position;
                /* trigger reload, not only conversion                                            */
                buffer->end                       = buffer->begin;
                /* iterator == end => trigger reload                                              */
                buffer->iterator                  = buffer->end;
                buffer->iterators_character_index = 0;
                __QuexBufferFiller_step_forward_n_characters((QuexBufferFiller*)me, Index);
                /* We can assume, that the index is reachable, since the current index is higher. */
                __quex_assert(buffer->iterators_character_index == Index);
            } 
        }
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    QUEX_INLINE bool 
    QuexBufferFiller_IConv_has_coding_dynamic_character_width(const char* Coding) 
    {
        return true; /* TODO: distinguish between different coding formats   */
        /*           //       'true' is safe, but possibly a little slower.  */
    }

    TEMPLATE_IN(InputHandleT) void   
    QuexBufferFiller_IConv_BufferInfo_init(TEMPLATED(QuexBufferFiller_IConv_BufferInfo)* me, 
                                           uint8_t* Begin, size_t SizeInBytes,
                                           STREAM_POSITION_TYPE(InputHandleT) StartPosition)
    {
        me->begin               = Begin;

        me->end                 = Begin;
        me->end_stream_position = StartPosition;

        me->memory_end                = Begin + (ptrdiff_t)SizeInBytes;
        /* iterator == end --> trigger reload */
        me->iterator                  = me->end;
        me->iterators_character_index = 0;

#       ifdef QUEX_OPTION_ASSERTS
        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        __QUEX_STD_memset((uint8_t*)Begin, (uint8_t)0xFF, SizeInBytes);
#       endif
    }

    TEMPLATE_IN(InputHandleT) void   
    QuexBufferFiller_IConv_hint_set(CHAR_INDEX_AND_STREAM_POSITION(InputHandleT)*  me, 
                                    size_t                                         CharacterIndex, 
                                    ptrdiff_t                                      Offset, 
                                    STREAM_POSITION_TYPE(InputHandleT)             StreamPosition)
    {
        me->character_index = CharacterIndex;
        me->offset          = Offset;
        me->stream_position = StreamPosition;
    }
#undef CLASS

#if ! defined(__QUEX_SETTING_PLAIN_C)
}
#endif

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>

#endif /* __INCLUDE_GUARD__QUEX_BUFFER_FILLER_CONVERTER_ICONV_I__ */
