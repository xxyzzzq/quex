/* -*- C++ -*-  vim: set syntax=cpp:
 * (C) 2007-2015 Frank-Rene Schaefer  */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__CONVERTER__BUFFER_FILLER_CONVERTER_I

#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/filler/BufferFiller>
#include <quex/code_base/buffer/filler/converter/BufferFiller_Converter>
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
QUEX_NAME(BufferFiller_Converter_delete_self)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
QUEX_NAME(BufferFiller_Converter_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego);

QUEX_INLINE bool   
QUEX_NAME(BufferFiller_Converter_seek_character_index)(QUEX_NAME(BufferFiller)*         alter_ego, 
                                                       const QUEX_TYPE_STREAM_POSITION  CharacterIndex); 
QUEX_INLINE size_t 
QUEX_NAME(BufferFiller_Converter_input_character_load)(QUEX_NAME(BufferFiller)* alter_ego,
                                                       QUEX_TYPE_CHARACTER*     RegionBeginP, 
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
                                      size_t                 RawMemorySize)
{ 
    QUEX_NAME(BufferFiller_Converter)*  me;
    __quex_assert(RawMemorySize >= 6);  /* UTF-8 char can be 6 bytes long    */

    /* The 'BufferFiller_Converter' is the same host for all converters.
     * Converters are pointed to by 'converter',                             */
    me = (QUEX_NAME(BufferFiller_Converter)*) \
          QUEXED(MemoryManager_allocate)(sizeof(QUEX_NAME(BufferFiller_Converter)),
                                         E_MemoryObjectType_BUFFER_FILLER);
    if( ! me) return me;

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
    uint8_t* raw_memory;

    QUEX_NAME(BufferFiller_setup)(&me->base,
                                  QUEX_NAME(BufferFiller_Converter_tell_character_index),
                                  QUEX_NAME(BufferFiller_Converter_seek_character_index), 
                                  QUEX_NAME(BufferFiller_Converter_input_character_load),
                                  QUEX_NAME(BufferFiller_Converter_delete_self),
                                  QUEX_NAME(BufferFiller_Converter_fill_prepare),
                                  QUEX_NAME(BufferFiller_Converter_fill_finish),
                                  byte_loader);

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
    const QUEX_TYPE_STREAM_POSITION    begin_character_index = raw->next_to_convert_character_index;
    ptrdiff_t                          converted_character_n;

    __quex_assert(me->converter);
    __quex_assert(alter_ego); 
    __quex_assert(RegionBeginP); 
    QUEX_ASSERT_BUFFER_INFO(raw);
    QUEX_IF_ASSERTS_poison(RegionBeginP, &RegionBeginP[N]);

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

        if( ! QUEX_NAME(__BufferFiller_Converter_fill_raw_buffer)(me) ) {
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

    converted_character_n = buffer_insertion_p - RegionBeginP;
    /* 'raw->next_to_convert_p' was updated by 'convert()'; and points behind
     * the last byte that was converted.                                     */ 
    raw->next_to_convert_character_index =  begin_character_index 
                                          + converted_character_n;

    if( converted_character_n != (ptrdiff_t)N ) {
        /* Buffer not filled completely; I.e. END OF FILE has been reached.  */
        __quex_assert(BufferEnd >= buffer_insertion_p);
        QUEX_IF_ASSERTS_poison(buffer_insertion_p, BufferEnd);
    }
    return (size_t)converted_character_n;
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
QUEX_NAME(BufferFiller_Converter_tell_character_index)(QUEX_NAME(BufferFiller)* alter_ego)
{ 
    QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;

    return me->raw_buffer.next_to_convert_character_index; 
}

QUEX_INLINE bool   
QUEX_NAME(BufferFiller_Converter_seek_character_index)(QUEX_NAME(BufferFiller)*         alter_ego, 
                                                       const QUEX_TYPE_STREAM_POSITION  CharacterIndex)

/* BufferFiller's seek sets the input position for the next character read in
 * the stream. That is, it adapts:
 *
 *     'next_to_convert_character_index = CharacterIndex' 
 *
 * The raw buffer and the byte loader are prepared in a way so that the next 
 * loading will start with 'CharacterIndex'. This task is not trivial, because
 * in general there is no linear relationship between the stream position of 
 * the byte loader and the index of the character to which it points.
 *
 * RETURNS: true upon success, false else.                                   */
{ 
    QUEX_NAME(BufferFiller_Converter)*  me  = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
    QUEX_NAME(RawBuffer)*               raw = &me->raw_buffer;
    ptrdiff_t                           ContentSize  = 0;

    __quex_assert(alter_ego); 
    __quex_assert(me->converter);
    QUEX_ASSERT_BUFFER_INFO(raw);

    if( me->byte_loader )                                    return false;
    else if( Index == raw->next_to_convert_character_index ) return true;

    /* Some converters (e.g. IBM's ICU) require to reset their state when 
     * conversion is discontinued,                                           */
    if( me->converter->on_conversion_discontinuity ) {
        me->converter->on_conversion_discontinuity(me->converter);
    }

    /* Codec => fixed or dynamic character width => two methods of seeking.  */
    if(    me->converter->byte_n_per_character != -1 
        && me->byte_loader->binary_mode_f ) { 
        /* Each character always occupies the same amount of bytes. 
         * => Offsets CAN be **computed**. This is FAST.                     */
        target =   byte_loader->initial_position 
                 + me->converter->byte_n_per_character * CharacterIndex;

        me->base.byte_loader->seek(me->base.byte_loader, target);
        if( me->base.byte_loader->tell(me->base.byte_loader) != target ) {
            return false;
        }
        
        /* next_to_convert_p == fill_end_p => trigger reload                 */
        raw->next_to_convert_p               = raw->fill_end_p;
        raw->next_to_convert_character_index = Index;
    } 
    else  { 
        /* Characters may occupy different amount of bytes. 
         * => offsets CANNOT be computed. 
         *
         * Conversion starts from a known position until 'CharacterIndex' is 
         * reached. Only known position: initial position. (TODO: may be add
         * a 'cache' of known previous positions)                            */
        me->base.byte_loader->seek(me->base.byte_loader, 
                                   me->base.byte_loader->initial_position);             

        raw->fill_end_p                      = raw->begin;                   
        /* next_to_convert_p == fill_end_p => trigger reload                 */
        raw->next_to_convert_p               = raw->fill_end_p;
        raw->next_to_convert_character_index = 0;
        QUEX_NAME(BufferFiller_step_forward_n_characters)(alter_ego,
                                                          (ptrdiff_t)CharacterIndex);
    }
    QUEX_ASSERT_BUFFER_INFO(raw);
    return true;
}

QUEX_INLINE size_t 
QUEX_NAME(__BufferFiller_Converter_fill_raw_buffer)(QUEX_NAME(BufferFiller_Converter)*  me) 
/* Try to fill the raw buffer to its limits with data from the file.  The
 * filling starts from its current position, thus the remaining bytes to be
 * translated are exactly the number of bytes in the buffer.                 */
{
    QUEX_NAME(RawBuffer)*  raw = &me->raw_buffer;
    uint8_t*               fill_begin_p;
    size_t                 fill_size;
    size_t                 loaded_n;

    __quex_assert(raw->next_to_convert_p <= raw->fill_end_p);
    QUEX_ASSERT_BUFFER_INFO(raw);

    /* Move content that has not yet been converted to the buffer's begin.   */
    QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(me);
    /* HERE: .next_to_convert_p = .begin                                     */

    fill_begin_p    = &raw->fill_end_p;
    fill_size       = (size_t)(raw->memory_end - fill_begin_p);

    loaded_n        = me->base.byte_loader->load(me->base.byte_loader, 
                                                 fill_begin_p, fill_size);
    raw->fill_end_p = &fill_begin_p[loaded_n];

    QUEX_ASSERT_BUFFER_INFO(raw);
    return loaded_n;
}


QUEX_INLINE void 
QUEX_NAME(BufferFiller_Converter_fill_prepare)(QUEX_NAME(Buffer)*  buffer,
                                               void**              begin_p,
                                               const void**        end_p)
{
    QUEX_NAME(BufferFiller_Converter)* me = (QUEX_NAME(BufferFiller_Converter)*)buffer->filler; 
    QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(me);

    *begin_p = (void*)me->raw_buffer.fill_end_p; 
    *end_p   = (void*)me->raw_buffer.memory_end;
}

QUEX_INLINE ptrdiff_t 
QUEX_NAME(BufferFiller_Converter_fill_finish)(QUEX_NAME(BufferFiller)*   alter_ego,
                                              QUEX_TYPE_CHARACTER*       RegionBeginP,,
                                              const QUEX_TYPE_CHARACTER* BufferEnd,
                                              const void*                FilledEndP)
/* Converts what has been filled into the 'raw_buffer' until 'FilledEndP
 * and stores it into the buffer.                                            */
{
    QUEX_NAME(BufferFiller_Converter)*  me = (QUEX_NAME(BufferFiller_Converter)*)alter_ego;
    QUEX_NAME(RawBuffer)*               raw = &me->raw_buffer;
    QUEX_TYPE_CHARACTER*                insertion_p = RegionBeginP;

    raw->fill_end_p = FilledEndP;   
    QUEX_ASSERT_BUFFER_INFO(raw);

    me->converter->convert(me->converter, 
                           &raw->next_to_convert_p, raw->fill_end_p,
                           &insertion_p,            BufferEnd);
    
    QUEX_ASSERT_BUFFER_INFO(raw);
    return insertion_p - RegionBeginP;
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_Converter_move_away_passed_content)(QUEX_NAME(BufferFiller_Converter)*  me)
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
    QUEX_NAME(RawBuffer)*  raw = &me->raw_buffer;
    uint8_t*               move_begin_p;
    ptrdiff_t              move_size;
    ptrdiff_t              move_distance;
   
    __quex_assert(raw->next_to_convert_p <= raw->fill_end_p);
    QUEX_ASSERT_BUFFER_INFO(raw);

    move_begin_p  = raw->next_to_convert_p;
    move_size     = raw->fill_end_p - raw->next_to_convert_p;
    move_distance = raw->next_to_convert_p - raw->begin;

    if( ! move_distance ) return;
    else if( move_size ) {
        __QUEX_STD_memmove((void*)raw->begin, (void*)move_begin_p, move_size);
    }

    raw->next_to_convert_p  = raw->begin; 
    raw->fill_end_p        -= move_distance;

    QUEX_IF_ASSERTS_poison(&raw->begin[remaining_byte_n], raw->memory_end);
    QUEX_ASSERT_BUFFER_INFO(raw);
}

QUEX_INLINE void   
QUEX_NAME(RawBuffer_init)(QUEX_NAME(RawBuffer)* me, 
                          uint8_t* Begin, size_t SizeInBytes)
{
    me->begin                           = Begin;
    me->fill_end_p                      = Begin;
    me->memory_end                      = &Begin[(ptrdiff_t)SizeInBytes];
    /* next_to_convert_p == fill_end_p --> trigger reload                    */
    me->next_to_convert_p               = me->fill_end_p;
    me->next_to_convert_character_index = 0;

    QUEX_IF_ASSERTS_poison(me->begin, me->memory_end);
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
