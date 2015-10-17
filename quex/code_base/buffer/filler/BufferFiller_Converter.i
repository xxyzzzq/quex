/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2015 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/filler/BufferFiller>
#include <quex/code_base/buffer/filler/BufferFiller_Converter>
#include <quex/code_base/compatibility/iconv-argument-types.h>


#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(BufferFiller_Converter_construct)(QUEX_NAME(BufferFiller_Converter)* me, 
                                            ByteLoader*            byte_loader,
                                            QUEX_NAME(Converter)*  converter,
                                            const char*            FromCoding,
                                            const char*            ToCoding,
                                            size_t                 RawMemorySize);

QUEX_INLINE void   
QUEX_NAME(BufferFiller_Converter_input_clear)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE void   
QUEX_NAME(BufferFiller_Converter_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE size_t 
QUEX_NAME(BufferFiller_Converter_input_character_load)(QUEX_NAME(BufferFiller)* alter_ego,
                                                       QUEX_TYPE_CHARACTER*     RegionBeginP, 
                                                       const size_t             N);
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
QUEX_INLINE void 
QUEX_NAME(RawBuffer_move_away_passed_content)(QUEX_NAME(RawBuffer)*  me);
QUEX_INLINE size_t 
QUEX_NAME(RawBuffer_load)(QUEX_NAME(RawBuffer)*  me, ByteLoader* byte_loader);

QUEX_INLINE QUEX_NAME(BufferFiller)*
QUEX_NAME(BufferFiller_Converter_new)(ByteLoader*            byte_loader,
                                      QUEX_NAME(Converter)*  converter,
                                      const char*            FromCoding,
                                      const char*            ToCoding,
                                      size_t                 RawMemorySize)
{ 
    QUEX_NAME(BufferFiller_Converter)*  me;
    __quex_assert(RawMemorySize >= 6);  /* UTF-8 char can be 6 bytes long    */

    /* The 'BufferFiller_Converter' is the same host for all converters.
     * Converters are pointed to by 'converter',                             */
    me = (QUEX_NAME(BufferFiller_Converter)*) \
          QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(BufferFiller_Converter)),
                                         E_MemoryObjectType_BUFFER_FILLER);
    if( ! me) return (QUEX_NAME(BufferFiller)*)0;

    QUEX_NAME(BufferFiller_Converter_construct)(me, byte_loader, converter, FromCoding, ToCoding, RawMemorySize);

    return &me->base;

}

QUEX_INLINE void
QUEX_NAME(BufferFiller_Converter_construct)(QUEX_NAME(BufferFiller_Converter)* me, 
                                            ByteLoader*            byte_loader,
                                            QUEX_NAME(Converter)*  converter,
                                            const char*            FromCoding,
                                            const char*            ToCoding,
                                            size_t                 RawMemorySize)
{
    /* A linear relationship between stream position and character index 
     * requires that: (1) The input stream is in 'binary mode'. That is, the 
     * stream position is proportional to the number of bytes that lie 
     * behind. (2) The input codec is of fixed size, i.e. 
     * converter->byte_n_per_character != -1.                                */ 
    ptrdiff_t   byte_n_per_character = byte_loader->binary_mode_f ? 
                                       converter->byte_n_per_character : -1;
    uint8_t*    raw_memory;

    QUEX_NAME(BufferFiller_setup)(&me->base,
                                  QUEX_NAME(BufferFiller_Converter_input_character_load),
                                  QUEX_NAME(BufferFiller_Converter_input_clear),
                                  QUEX_NAME(BufferFiller_Converter_delete_self),
                                  QUEX_NAME(BufferFiller_Converter_fill_prepare),
                                  QUEX_NAME(BufferFiller_Converter_fill_finish),
                                  byte_loader,
                                  byte_n_per_character);

    /* Initialize the conversion operations                                  */
    me->converter = converter;
    me->converter->open(me->converter, FromCoding, ToCoding);
    me->converter->virginity_f = true;

    /* Initialize the raw buffer that holds the plain bytes of the input file
     * (setup to trigger initial reload)                                     */
    raw_memory = QUEXED(MemoryManager_allocate)(RawMemorySize, 
                                                E_MemoryObjectType_BUFFER_RAW);
    QUEX_NAME(RawBuffer_init)(&me->raw_buffer, raw_memory, RawMemorySize);

    QUEX_ASSERT_BUFFER_INFO(&me->raw_buffer);
}

QUEX_INLINE void   
QUEX_NAME(BufferFiller_Converter_input_clear)(QUEX_NAME(BufferFiller)* alter_ego)
{
    QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;

    if( me->converter->input_clear ) me->converter->input_clear(me->converter);
    QUEX_NAME(RawBuffer_init)(&me->raw_buffer, 0, 0);
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
QUEX_NAME(BufferFiller_Converter_input_character_load)(QUEX_NAME(BufferFiller)*  alter_ego,
                                                       QUEX_TYPE_CHARACTER*      RegionBeginP, 
                                                       const size_t              N)
/* Loads content into the raw buffer, convert it and write it to the engine's
 * buffer. The region where to write into the engine's buffer expands from
 * 'RegionBeginP' to 'N' characters after it.                                */
{
    QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
    QUEX_NAME(RawBuffer)*              raw = &me->raw_buffer;
    QUEX_TYPE_CHARACTER*               buffer_insertion_p    = RegionBeginP;
    const QUEX_TYPE_CHARACTER*         BufferEnd             = &RegionBeginP[N];
    ptrdiff_t                          converted_character_n;

    __quex_assert(me->converter);
    __quex_assert(alter_ego); 
    __quex_assert(RegionBeginP); 
    QUEX_ASSERT_BUFFER_INFO(raw);
    /* NOT: QUEX_IF_ASSERTS_poison(RegionBeginP, &RegionBeginP[N]);
     * The buffer must remain intact, in case that not all is loaded.        */

    /* Some converters keep some content internally. So, it is a more general
     * solution to convert first and reload new bytes upon need.             */
    while( 1 + 1 == 2 ) {
        /* NOT: if( next_to_convert_p != fill_end_p ) ...
         * Because, converters may leave some content in their stomach and spit
         * it out later (e.g. ICU).                                          */
        if( me->converter->convert(me->converter, 
                                   &raw->next_to_convert_p, raw->fill_end_p,
                                   &buffer_insertion_p,     BufferEnd) ) {
            break;
        }

        __quex_assert(buffer_insertion_p < BufferEnd);  /* '==' means break  */
        QUEX_ASSERT_BUFFER_INFO(raw); 

        if( ! QUEX_NAME(RawBuffer_load)(&me->raw_buffer, me->base.byte_loader) ) {
            /* No bytes have been loaded.                                    */
            if( raw->fill_end_p != raw->begin ) {
                /* There are still bytes, but they were not converted by the 
                 * converter.                                                */
                QUEX_ERROR_EXIT("Error. At end of file, byte sequence not interpreted as character.");
            }
            break;
        }
    }
    me->converter->virginity_f = false;

    /* 'buffer_insertion_p' was updated by 'convert' and points behind the 
     * last byte that was converted.                                         */ 
    converted_character_n = buffer_insertion_p - RegionBeginP;
    me->base.character_index_next_to_fill += converted_character_n;

    if( converted_character_n != (ptrdiff_t)N ) {
        /* Buffer not filled completely; I.e. END OF FILE has been reached.  */
        __quex_assert(BufferEnd >= buffer_insertion_p);
        QUEX_IF_ASSERTS_poison(buffer_insertion_p, BufferEnd);
    }
    return (size_t)converted_character_n;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Converter_fill_prepare)(QUEX_NAME(Buffer)*  buffer,
                                               void**              begin_p,
                                               const void**        end_p)
{
    QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)buffer->filler; 
    QUEX_NAME(RawBuffer_move_away_passed_content)(&me->raw_buffer);

    *begin_p = (void*)me->raw_buffer.fill_end_p; 
    *end_p   = (void*)me->raw_buffer.memory_end;
}

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Converter_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                              QUEX_TYPE_CHARACTER*       RegionBeginP,
                                              const QUEX_TYPE_CHARACTER* BufferEnd,
                                              const void*                FilledEndP)
/* Converts what has been filled into the 'raw_buffer' until 'FilledEndP
 * and stores it into the buffer.                                            */
{
    QUEX_NAME(BufferFiller_Converter)*  me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
    QUEX_NAME(RawBuffer)*               raw = &me->raw_buffer;
    QUEX_TYPE_CHARACTER*                insertion_p = RegionBeginP;

    raw->fill_end_p = (uint8_t*)FilledEndP;   
    QUEX_ASSERT_BUFFER_INFO(raw);

    me->converter->convert(me->converter, 
                           &raw->next_to_convert_p, raw->fill_end_p,
                           &insertion_p,            BufferEnd);
    
    QUEX_ASSERT_BUFFER_INFO(raw);
    return insertion_p - RegionBeginP;
}

QUEX_INLINE void   
QUEX_NAME(RawBuffer_init)(QUEX_NAME(RawBuffer)* me, 
                          uint8_t* Begin, size_t SizeInBytes)
/* Initialize raw buffer. 
 * (1) Begin != 0 => Assign memory. 
 * (2) Begin == 0 => Only reset pointers, so buffer is 'empty'.              */
{
    if( Begin ) {
        me->begin      = Begin;
        me->memory_end = &Begin[(ptrdiff_t)SizeInBytes];
    }
    me->fill_end_p        = me->begin;
    me->next_to_convert_p = me->begin;                /* --> trigger reload. */

    QUEX_IF_ASSERTS_poison(me->begin, me->memory_end);
}

QUEX_INLINE void 
QUEX_NAME(RawBuffer_move_away_passed_content)(QUEX_NAME(RawBuffer)*  me)
/* Consider any content in the raw buffer from begin to 'next_to_convert_p' as
 * passed and useless. Thus, move what comes behind to the beginning of the 
 * buffer. Adapt:
 *
 *     -- '.fill_end_p'
 *     -- '.next_to_convert_p'
 *
 * The relation of '.next_to_convert_p' and '.next_to_convert_character_index' 
 * remains unaffected. The pointer still points to the same character index. */
{
    uint8_t*               move_begin_p;
    ptrdiff_t              move_size;
    ptrdiff_t              move_distance;
   
    __quex_assert(me->next_to_convert_p <= me->fill_end_p);
    QUEX_ASSERT_BUFFER_INFO(me);

    move_begin_p  = me->next_to_convert_p;
    move_size     = me->fill_end_p - me->next_to_convert_p;
    move_distance = me->next_to_convert_p - me->begin;

    if( ! move_distance ) return;
    else if( move_size ) {
        __QUEX_STD_memmove((void*)me->begin, (void*)move_begin_p, move_size);
    }

    me->next_to_convert_p  = me->begin; 
    me->fill_end_p        -= move_distance;

    QUEX_IF_ASSERTS_poison(me->fill_end_p, me->memory_end);
    QUEX_ASSERT_BUFFER_INFO(me);
}

QUEX_INLINE size_t 
QUEX_NAME(RawBuffer_load)(QUEX_NAME(RawBuffer)*  me,
                          ByteLoader*            byte_loader) 
/* Try to fill the me buffer to its limits with data from the file.  The
 * filling starts from its current position, thus the remaining bytes to be
 * translated are exactly the number of bytes in the buffer.                 */
{
    uint8_t*  fill_begin_p;
    size_t    fill_size;
    size_t    loaded_byte_n;

    QUEX_ASSERT_BUFFER_INFO(me);

    /* Move content that has not yet been converted to the buffer's begin.   */
    QUEX_NAME(RawBuffer_move_away_passed_content)(me);

    fill_begin_p    = me->fill_end_p;
    fill_size       = (size_t)(me->memory_end - fill_begin_p);
    loaded_byte_n   = byte_loader->load(byte_loader, fill_begin_p, fill_size);
    me->fill_end_p  = &fill_begin_p[loaded_byte_n];

    QUEX_ASSERT_BUFFER_INFO(me);
    return loaded_byte_n;
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#include <quex/code_base/buffer/filler/BufferFiller.i>

#include <quex/code_base/buffer/filler/converter/Converter.i>

#ifdef QUEX_OPTION_CONVERTER_ICONV
#   include <quex/code_base/buffer/filler/converter/iconv/Converter_IConv.i>
#endif
#ifdef QUEX_OPTION_CONVERTER_ICU
#   include <quex/code_base/buffer/filler/converter/icu/Converter_ICU.i>
#endif


#endif /* __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I */
