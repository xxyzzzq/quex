/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2008 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/converter/BufferFiller_Converter>
#include <quex/code_base/compatibility/iconv-argument-types.h>


#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN
    QUEX_INLINE void
    QUEX_NAME(BufferFiller_Converter_construct)(QUEX_NAME(BufferFiller_Converter)* me, 
                                                ByteLoader*          byte_loader,
                                                QUEX_NAME(Converter)*  converter,
                                                const char*            FromCoding,
                                                const char*            ToCoding,
                                                size_t                 RawBufferSize);

    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Converter_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

    QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
    QUEX_NAME(BufferFiller_Converter_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego);
    
    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Converter_seek_character_index)(QUEX_NAME(BufferFiller)*         alter_ego, 
                                                           const QUEX_TYPE_STREAM_POSITION  CharacterIndex); 
    QUEX_INLINE size_t 
    QUEX_NAME(BufferFiller_Converter_read_characters)(QUEX_NAME(BufferFiller)* alter_ego,
                                                      QUEX_TYPE_CHARACTER*     start_of_buffer, 
                                                      const size_t             N);
    QUEX_INLINE size_t 
    QUEX_NAME(__BufferFiller_Converter_fill_raw_buffer)(QUEX_NAME(BufferFiller_Converter)*  me);

    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Converter_fill_prepare)(QUEX_NAME(Buffer)*  me,
                                                   void**              begin_p,
                                                   const void**        end_p);

    QUEX_INLINE ptrdiff_t 
    QUEX_NAME(BufferFiller_Converter_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                                  QUEX_TYPE_CHARACTER*       insertion_p,
                                                  const QUEX_TYPE_CHARACTER* BufferEnd,
                                                  const void*                ContentEnd);

    QUEX_INLINE void   
    QUEX_NAME(RawBuffer_init)(QUEX_NAME(RawBuffer)* me, 
                              uint8_t* Begin, size_t SizeInBytes);

    QUEX_INLINE QUEX_NAME(BufferFiller)*
    QUEX_NAME(BufferFiller_Converter_new)(ByteLoader*            byte_loader,
                                          QUEX_NAME(Converter)*  converter,
                                          const char*            FromCoding,
                                          const char*            ToCoding,
                                          size_t                 RawBufferSize)
    { 
        QUEX_NAME(BufferFiller_Converter)*  me;
        __quex_assert(RawBufferSize >= 6);  /* UTF-8 char can be 6 bytes long*/

        /* The 'BufferFiller_Converter' is the same host for all converters.
         * Converters are pointed to by 'converter',                         */
        me = (QUEX_NAME(BufferFiller_Converter)*) \
              QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(BufferFiller_Converter)),
                                             E_MemoryObjectType_BUFFER_FILLER);
        __quex_assert(me);

        QUEX_NAME(BufferFiller_Converter_construct)(me, byte_loader, converter, FromCoding, ToCoding, RawBufferSize);

        return &me->base;

    }

    QUEX_INLINE void
    QUEX_NAME(BufferFiller_Converter_construct)(QUEX_NAME(BufferFiller_Converter)* me, 
                                                ByteLoader*            byte_loader,
                                                QUEX_NAME(Converter)*  converter,
                                                const char*            FromCoding,
                                                const char*            ToCoding,
                                                size_t                 RawBufferSize)
    {
        uint8_t* raw_buffer_p;

        QUEX_NAME(BufferFiller_setup)(&me->base,
                                      QUEX_NAME(BufferFiller_Converter_tell_character_index),
                                      QUEX_NAME(BufferFiller_Converter_seek_character_index), 
                                      QUEX_NAME(BufferFiller_Converter_read_characters),
                                      QUEX_NAME(BufferFiller_Converter_delete_self),
                                      QUEX_NAME(BufferFiller_Converter_fill_prepare),
                                      QUEX_NAME(BufferFiller_Converter_fill_finish),
                                      byte_loader);

        /* Initialize the conversion operations                                             */
        me->converter = converter;
        me->converter->open(me->converter, FromCoding, ToCoding);
        me->converter->virginity_f = true;

        /* Initialize the raw buffer that holds the plain bytes of the input file
         * (setup to trigger initial reload)                                                */
        raw_buffer_p = QUEXED(MemoryManager_allocate)(RawBufferSize, 
                                                      E_MemoryObjectType_BUFFER_RAW);
        QUEX_NAME(RawBuffer_init)(&me->raw_buffer, raw_buffer_p, RawBufferSize);

        /* Hint for relation between character index, raw buffer offset and stream position */
        me->hint_begin_character_index = (ptrdiff_t)-1;

        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_CONSTRUCTOR(FromCoding, ToCoding, me->iconv_handle);*/
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Converter_delete_self)(QUEX_NAME(BufferFiller)* alter_ego)
    { 
        QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;

        if( ! me )                                                    return;
        else if( me->base.ownership != E_Ownership_LEXICAL_ANALYZER ) return;

        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);

        ByteLoader_delete(&me->base.byte_loader);
        QUEX_NAME(Converter_delete)(&me->converter); 

        QUEXED(MemoryManager_free)((void*)me->raw_buffer.begin,
                                   E_MemoryObjectType_BUFFER_RAW); 

        QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_BUFFER_FILLER);
    }

    QUEX_INLINE size_t 
    QUEX_NAME(BufferFiller_Converter_read_characters)(QUEX_NAME(BufferFiller)*  alter_ego,
                                                      QUEX_TYPE_CHARACTER*      user_memory_p, 
                                                      const size_t              N)
    {
        QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;

        /* TWO CASES:
         * (1) There are still some bytes in the raw buffer from the last load.
         *     in this case, first translate them and then maybe load the raw buffer
         *     again. (iterator != end)
         *
         * (2) The raw buffer is empty. Then it must be loaded in order to get some
         *     basis for conversion. For 'stateless' converters the condition
         *
         *                iterator == end
         *
         *     would be sufficient. However, there are converters that store some
         *     source data even if they report that 'iterator==end'. The final decision
         *     is left to the converter in its first call to 'convert()'. The 
         *     assumption 'iterator == end => reload required' does not hold here for the 
         *     general case.                                                              
         *                       
         *     If we wanted to do a pre-load here, this would increase complexity.
         *     Because one would need to communicate with the converter, wether there are
         *     some hidden bytes in the pipe. The task to determine this might also
         *     not be trivial for one or the other converter to be plugged in here.
         *
         *     THUS: No pre-load before the first conversion, even if the first conversion
         *           runs on zero bytes!                                                    */

        QUEX_TYPE_CHARACTER*             buffer_insertion_p   = user_memory_p;
        const QUEX_TYPE_CHARACTER*       BufferEnd            = &user_memory_p[N];
        const QUEX_TYPE_STREAM_POSITION  StartCharacterIndex  = me->raw_buffer.iterators_character_index;
        ptrdiff_t                        ConvertedCharN       = 0;

        __quex_assert(me->converter);
        __quex_assert(alter_ego); 
        __quex_assert(user_memory_p); 
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
#       ifdef QUEX_OPTION_ASSERTS
        __QUEX_STD_memset((uint8_t*)user_memory_p, 0xFF, N * sizeof(QUEX_TYPE_CHARACTER));
#       endif

        while( 1 + 1 == 2 ) {
            /* NOT: if( me->raw_buffer.iterator != me->raw_buffer.end ) ...
             * Because, some converters may leave some content in their stomach
             * and spit it out later (e.g. ICU).                             */
            if( me->converter->convert(me->converter, 
                                       &me->raw_buffer.iterator, me->raw_buffer.end,
                                       &buffer_insertion_p, BufferEnd) ) {
                me->converter->virginity_f = false;
                break;
            }

            __quex_assert(buffer_insertion_p < BufferEnd); /* '==' means break */
            QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);

            /* The raw buffer filler requires the iterator's character index to be up-to-date. */
            me->raw_buffer.iterators_character_index =   StartCharacterIndex 
                                                       + (buffer_insertion_p - user_memory_p);

            if( ! QUEX_NAME(__BufferFiller_Converter_fill_raw_buffer)(me) ) {
                /* No bytes have been loaded. */
                if( me->raw_buffer.end != me->raw_buffer.begin ) {
                    /* There are still bytes, but they were not converted by the converter. */
                    QUEX_ERROR_EXIT("Error. At end of file, byte sequence not interpreted as character.");
                }
                break;
            }
        }
        me->converter->virginity_f = false;

        ConvertedCharN = buffer_insertion_p - user_memory_p;
        me->raw_buffer.iterators_character_index = StartCharacterIndex + ConvertedCharN;

        if( ConvertedCharN != (ptrdiff_t)N ) {
            /* The buffer was not filled completely, because the end of the file was reached.   */
            __quex_assert(BufferEnd >= buffer_insertion_p);
            QUEX_IF_ASSERTS_poison(buffer_insertion_p, BufferEnd);
        }
        return (size_t)ConvertedCharN;
    }

    QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
    QUEX_NAME(BufferFiller_Converter_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego)
    { 
        QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
        __quex_assert(alter_ego); 

        /* The raw buffer iterator stands on the next character to be read. In general it holds
         * that the raw_buffer's iterator points to the first byte of the next character to be
         * converted when the next user buffer is to be filled.                                      */
        return me->raw_buffer.iterators_character_index; 
    }

    QUEX_INLINE void   
    QUEX_NAME(BufferFiller_Converter_seek_character_index)(QUEX_NAME(BufferFiller)*  alter_ego, 
                                                           const QUEX_TYPE_STREAM_POSITION           Index)
    { 
        /* The goal of the 'seek' is that the next filling of the user buffer starts at 
         * the specified character index 'Index'. This can be achieved by setting the 
         * raw buffer iterator.       
         *                                                                                        */
        /* NOTE: This differs from QuexBuffer_seek(...) in the sense, that it only sets the
         *       stream to a particular position given by a character index. QuexBuffer_seek(..)
         *       sets the _input_p to a particular position.                                      */
        QUEX_NAME(BufferFiller_Converter)*  me     = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
        QUEX_NAME(RawBuffer)*               buffer = &me->raw_buffer;
        /* NOTE: The 'hint' always relates to the begin of the raw buffer, see [Ref 1].           */
        const QUEX_TYPE_STREAM_POSITION     Hint_Index   = me->hint_begin_character_index;
        QUEX_TYPE_STREAM_POSITION           EndIndex     = 0;
        uint8_t*         Hint_Pointer = buffer->begin;
        ptrdiff_t        ContentSize  = 0;
        uint8_t*         new_iterator = 0;

        __quex_assert(alter_ego != 0x0); 
        __quex_assert(me->converter != 0x0);

        /* Seek_character_index(Pos) means that the next time when a character buffer
         * is to be filled, this has to happen from position 'CharacterIndex'. 
         *
         * NOTE: The reference for character positioning is **not** directly the stream.
         * Moreover, it is the internal raw_buffer.position. It determines what characters 
         * are converted next into the user's buffer.                                             */
        if( Index == buffer->iterators_character_index ) { 
            return;                                                /* Nothing to be done          */
        }
        /* Some type of converters (actually, at the time of this writing, only IBM's ICU)
         * require a reset as soon as the conversion is discontinued, i.e. the stream of
         * character's is disrupted. The reset happens to cope with some internal 'statefulness'. */
        if( me->converter->on_conversion_discontinuity ) {
            me->converter->on_conversion_discontinuity(me->converter);
        }

        /* Depending on the character encoding, the seek procedure can be optimized. There are the 
         * following two cases:
         *
         *   (1) The coding uses **fixed** character widths (such as ASCII, UCS2, UCS4, etc.) where
         *       each character always occupies the same amount of bytes. Here, offsets can be 
         *       **computed**. This makes things faster.
         *   (2) The coding uses **dynamic** character width (e.g. UTF-8). Here the position cannot
         *       be computed. Instead, the conversion must start from a given 'known' position 
         *       until one reaches the specified character index.                                 */
        if( ! me->converter->dynamic_character_size_f ) { 
            /* (1) Fixed Character Width */
            __quex_assert(buffer->end >= buffer->begin);
            ContentSize = buffer->end - buffer->begin;
            EndIndex    = Hint_Index + (ContentSize / (ptrdiff_t)sizeof(QUEX_TYPE_CHARACTER));
            /* NOTE: the hint index must be valid (i.e. != -1) */
            if( Index >= Hint_Index && Index < EndIndex && Hint_Index != (ptrdiff_t)-1 ) {
                new_iterator  = buffer->begin + (Index - Hint_Index) * (ptrdiff_t)sizeof(QUEX_TYPE_CHARACTER);
                buffer->iterator                  = new_iterator;
                buffer->iterators_character_index = Index;
            }
            else  /* Index not in [BeginIndex:EndIndex) */ {
                QUEX_TYPE_STREAM_POSITION new_start_position =
                    (QUEX_TYPE_STREAM_POSITION)((size_t)Index * sizeof(QUEX_TYPE_CHARACTER));
                /* Seek stream position cannot be handled when buffer based analyzis is on.       */
                if( me->base.byte_loader ) {
                    me->base.byte_loader->seek(me->base.byte_loader, new_start_position);
                    __quex_assert(new_start_position == me->base.byte_loader->tell(me->base.byte_loader));
                }
                /* iterator == end => trigger reload                                              */
                buffer->iterator                  = buffer->end;
                buffer->iterators_character_index = Index;
            }
        } 
        else  { 
            /* (2) Dynamic Character Width */
            /* Setting the iterator to the begin of the raw_buffer initiates a conversion
             * start from this point.                                                             */
            /* NOTE: the hint index must be valid (i.e. != -1) */
            if( Index == Hint_Index && Hint_Index != (ptrdiff_t)-1 ) { 
                /* The 'read_characters()' function works on the content of the bytes
                 * in the raw_buffer. The only thing that has to happen is to reset 
                 * the raw buffer's position pointer to '0'.                                      */
                buffer->iterators_character_index = Index;
                buffer->iterator                  = Hint_Pointer;
            }
            else if( Index > Hint_Index && Hint_Index != (ptrdiff_t)-1 ) { 
                /* The searched index lies in the current raw_buffer or behind. Simply start 
                 * conversion from the current position until it is reached--but use the stuff 
                 * currently inside the buffer.                                                   */
                buffer->iterators_character_index = Hint_Index;
                buffer->iterator                  = Hint_Pointer;
                QUEX_NAME(BufferFiller_step_forward_n_characters)((QUEX_NAME(BufferFiller)*)me, 
                                                                  (ptrdiff_t)(Index - Hint_Index));
                /* assert on index position, see end of 'step_forward_n_characters(...)'.         */
            }
            else  /* Index < BeginIndex */ {
                /* No idea where to start --> start from the beginning. In some cases this might
                 * mean a huge performance penalty. But note, that this only occurs at pre-conditions
                 * that are very very long and happen right at the beginning of the raw buffer.   */

                /* Seek stream position cannot be handled when buffer based analyzis is on.       */
                if( me->base.byte_loader ) {
                    me->base.byte_loader->seek(me->base.byte_loader, 0);
                }
                /* trigger reload, not only conversion                                            */
                buffer->end                       = buffer->begin;
                /* iterator == end => trigger reload                                              */
                buffer->iterator                  = buffer->end;
                buffer->iterators_character_index = 0;
                QUEX_NAME(BufferFiller_step_forward_n_characters)((QUEX_NAME(BufferFiller)*)me, 
                                                                  (ptrdiff_t)Index);
                /* We can assume, that the index is reachable, since the current index is higher. */
                __quex_assert(buffer->iterators_character_index == Index);
            } 
        }
        QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
    }

    QUEX_INLINE size_t 
    QUEX_NAME(__BufferFiller_Converter_fill_raw_buffer)(QUEX_NAME(BufferFiller_Converter)*  me) 
    {
       /* Try to fill the raw buffer to its limits with data from the file.
        * The filling starts from its current position, thus the remaining bytes
        * to be translated are exactly the number of bytes in the buffer.              */
       QUEX_NAME(RawBuffer)*  buffer            = &me->raw_buffer;
       size_t                 remaining_byte_n;
       uint8_t*               FillStartPosition = 0;
       size_t                 FillSize          = 0;
       size_t                 LoadedByteN       = 0;

       __quex_assert(buffer->iterator <= buffer->end);

       remaining_byte_n = (size_t)(buffer->end - buffer->iterator);

       QUEX_ASSERT_BUFFER_INFO(buffer);
       __quex_assert((size_t)(buffer->end - buffer->begin) >= remaining_byte_n);

       /* Store information about the current position's character index. 
        * [Ref 1] -- 'end' may point point into the middle of an (not yet converted) character. 
        *         -- 'iterator' points always to the first byte after the last interpreted char.
        *         -- The stretch starting with 'iterator' to 'end - 1' contains the fragment
        *            of the uninterpreted character.
        *         -- The stretch of the uninterpreted character fragment is to be copied 
        *            to the  beginning of the buffer. 
        *  
        *         ==> The character index of the iterator relates always to the begin of 
        *             the buffer.
        */

       /* NOTE: Some converters contain a weird statefulness. Let us assume
        *       that if the converter has a 'on_conversion_discontinuity()'
        *       function, then no good assumptions can be made about character 
        *       index and buffer position.  (Currently only ICU converters 
        *       behave so strangely.                                         */

       if( ! me->converter->on_conversion_discontinuity ) {
           me->hint_begin_character_index = buffer->iterators_character_index;
       }

       /* There are cases (e.g. when a broken multibyte sequence occured at the end of 
        * the buffer) where there are bytes left in the raw buffer. These need to be
        * moved to the beginning of the buffer.                                        */
       if( remaining_byte_n ) {
           /* Be careful: Maybe one can use 'memcpy()' which is a bit faster but the
            * following is safe against overlaps.                                      */
           /* Cast to uint8_t to avoid a spurious function overload                    */
           __QUEX_STD_memmove((uint8_t*)(buffer->begin), (uint8_t*)(buffer->iterator), remaining_byte_n);
       }

       FillStartPosition = buffer->begin + remaining_byte_n;
       FillSize          = (size_t)(buffer->memory_end - buffer->begin) - remaining_byte_n;
       /* We cannot load bytes, if buffer based analyzis is on.                        */
       if( me->base.byte_loader ) {
           LoadedByteN                 = me->base.byte_loader->load(me->base.byte_loader, FillStartPosition, FillSize);
       }
       /* '.character_index' remains to be updated after character conversion */

       /* In any case, we start reading from the beginning of the raw buffer. */
       buffer->iterator = buffer->begin; 
       buffer->end      = &buffer->begin[LoadedByteN + remaining_byte_n];

       /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_BUFFER_LOAD(LoadedByteN);*/
       QUEX_ASSERT_BUFFER_INFO(buffer);

       return LoadedByteN;
    }


    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Converter_fill_prepare)(QUEX_NAME(Buffer)*  buffer,
                                                   void**              begin_p,
                                                   const void**        end_p)
    {
        QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)buffer->filler; 
        QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(me);

        *begin_p = (void*)me->raw_buffer.end; 
        *end_p   = (void*)me->raw_buffer.memory_end;
    }

    QUEX_INLINE ptrdiff_t 
    QUEX_NAME(BufferFiller_Converter_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                                  QUEX_TYPE_CHARACTER*       insertion_p,
                                                  const QUEX_TYPE_CHARACTER* BufferEnd,
                                                  const void*                FilledEndP)
        /* Appends the content first into a 'raw' buffer and then converts it. This
         * is useful in cases where the 'break' may appear in between characters, or
         * where the statefulness of the converter cannot be controlled.              */
    {
        QUEX_NAME(BufferFiller_Converter)*  me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
        QUEX_TYPE_CHARACTER*                insertion_begin_p = insertion_p;
        const uint8_t*                      EndP = (const uint8_t*)FilledEndP;

        __quex_assert(me->raw_buffer.iterator <= me->raw_buffer.end);
        __quex_assert(EndP >= me->raw_buffer.iterator);
        __quex_assert(EndP <= me->raw_buffer.end);

        /* (2) Convert data from the 'raw' buffer into the analyzer buffer.             */

        /*     -- Perform the conversion.                                               */
        me->converter->convert(me->converter, 
                               &me->raw_buffer.iterator, EndP,
                               &insertion_p,             BufferEnd);

        me->raw_buffer.iterator = (uint8_t*)EndP;
        
        return insertion_p - insertion_begin_p;
    }

    QUEX_INLINE void 
    QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(QUEX_NAME(BufferFiller_Converter)*  me)
    /* Service function for 'direct buffer' access to the lexical analyzer. */
    {
        QUEX_NAME(RawBuffer)*  buffer          = &me->raw_buffer;
        size_t                 remaining_byte_n;
       
        __quex_assert(buffer->iterator <= buffer->end);
        remaining_byte_n = (size_t)(buffer->end - buffer->iterator);

        QUEX_ASSERT_BUFFER_INFO(buffer);
        __quex_assert((size_t)(buffer->end - buffer->begin) >= remaining_byte_n);

        /* There are cases (e.g. when a broken multibyte sequence occured at the end of 
         * the buffer) where there are bytes left in the raw buffer. These need to be
         * moved to the beginning of the buffer.                                        */
        if( remaining_byte_n ) {
            /* Be careful: Maybe one can use 'memcpy()' which is a bit faster but the
             * following is safe against overlaps.                                      */
            /* Cast to uint8_t to avoid a spurious function overload                    */
            __QUEX_STD_memmove((uint8_t*)(buffer->begin), (uint8_t*)(buffer->iterator), 
                               remaining_byte_n);
        }

        /* In any case, we start reading from the beginning of the raw buffer. */
        buffer->iterator = buffer->begin; 
        buffer->end      = &buffer->begin[remaining_byte_n];

#       ifdef QUEX_OPTION_ASSERTS
        __quex_assert((size_t)(buffer->memory_end - buffer->begin) >= remaining_byte_n);
        __QUEX_STD_memset((uint8_t*)(buffer->begin) + remaining_byte_n, 0xFF, 
                          (size_t)(buffer->memory_end - buffer->begin) - remaining_byte_n);
#       endif
        /*QUEX_UNIT_TEST_ICONV_INPUT_STRATEGY_PRINT_RAW_BUFFER_LOAD(LoadedByteN);*/
        QUEX_ASSERT_BUFFER_INFO(buffer);
    }

    QUEX_INLINE void   
    QUEX_NAME(RawBuffer_init)(QUEX_NAME(RawBuffer)* me, 
                              uint8_t* Begin, size_t SizeInBytes)
    {
        me->begin               = Begin;
        me->end                 = Begin;
        me->memory_end          = &Begin[(ptrdiff_t)SizeInBytes];
        /* iterator == end --> trigger reload */
        me->iterator                  = me->end;
        me->iterators_character_index = 0;

#       ifdef QUEX_OPTION_ASSERTS
        /* Cast to uint8_t to avoid that some smart guy provides a C++ overloading function */
        __QUEX_STD_memset((uint8_t*)Begin, (uint8_t)0xFF, SizeInBytes);
#       endif
    }

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/BufferFiller.i>

#include <quex/code_base/buffer/converter/Converter.i>

#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/converter/icu/Converter_ICU.i>
#endif


#endif /* __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I */
