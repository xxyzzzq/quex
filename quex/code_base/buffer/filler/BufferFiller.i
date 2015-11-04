/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/filler/BufferFiller>
#include <quex/code_base/buffer/Buffer_debug>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE bool       QUEX_NAME(BufferFiller_character_index_seek)(QUEX_NAME(BufferFiller)*         me, 
                                                                    const QUEX_TYPE_STREAM_POSITION  CharacterIndex);
QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
                       QUEX_NAME(BufferFiller_character_index_tell)(QUEX_NAME(BufferFiller)* me);
QUEX_INLINE bool       QUEX_NAME(BufferFiller_character_index_step_to)(QUEX_NAME(BufferFiller)*        me,
                                                                       const QUEX_TYPE_STREAM_POSITION TargetCI);
QUEX_INLINE void       QUEX_NAME(BufferFiller_character_index_reset)(QUEX_NAME(BufferFiller)* me);
QUEX_INLINE void       QUEX_NAME(BufferFiller_character_index_reset_backup)(QUEX_NAME(BufferFiller)* me, 
                                                          QUEX_TYPE_STREAM_POSITION Backup_character_index_next_to_fill, 
                                                          ptrdiff_t                 BackupStomachByteN, 
                                                          QUEX_TYPE_STREAM_POSITION BackupByteLoaderPosition);

QUEX_INLINE void*      QUEX_NAME(BufferFiller_fill)(QUEX_NAME(Buffer)* buffer, 
                                                    const void*        ContentBegin, 
                                                    const void*        ContentEnd);
QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_prepare)(QUEX_NAME(Buffer)*  buffer, 
                                                            void**              begin_p, 
                                                            const void**        end_p);
QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_finish)(QUEX_NAME(Buffer)* buffer,
                                                           const void*        FilledEndP);
QUEX_INLINE void       QUEX_NAME(__BufferFiller_on_overflow)(QUEX_NAME(Buffer)*, bool ForwardF);

                       
QUEX_INLINE QUEX_NAME(BufferFiller)*
QUEX_NAME(BufferFiller_new)(ByteLoader*           byte_loader, 
                            QUEX_NAME(Converter)* converter,
                            const size_t          TranslationBufferMemorySize)
{
    QUEX_NAME(BufferFiller)* filler;
    (void)TranslationBufferMemorySize;

    /* byte_loader = 0; possible if memory is filled manually.               */
    if( converter ) {
        filler = QUEX_NAME(BufferFiller_Converter_new)(byte_loader, converter, 
                                                       TranslationBufferMemorySize);
    }
    else {
        filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader); 
    }
    
    return filler;
}

QUEX_INLINE QUEX_NAME(BufferFiller)* 
QUEX_NAME(BufferFiller_new_DEFAULT)(ByteLoader*   byte_loader, 
                                    const char*   InputCodecName) 
{
#   if   defined(QUEX_OPTION_CONVERTER_ICONV)
    QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_IConv_new)(InputCodecName, 0);
#   elif defined(QUEX_OPTION_CONVERTER_ICU)
    QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_ICU_new)(InputCodecName, 0);
#   else
    QUEX_NAME(Converter)* converter = (QUEX_NAME(Converter)*)0;
#   endif

    if( converter ) {
        converter->ownership = E_Ownership_LEXICAL_ANALYZER;
        if( ! InputCodecName ) {
#           ifndef QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED
            __QUEX_STD_printf("Warning: No character encoding name specified, while this\n" \
                              "Warning: analyzer was generated for use with a converter.\n" \
                              "Warning: Please, consult the documentation about the constructor\n" \
                              "Warning: or the reset function. If it is desired to do a plain\n" \
                              "Warning: buffer filler with this setup, you might want to disable\n" \
                              "Warning: this warning with the macro:\n" \
                              "Warning:     QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED\n");
#           endif
            return (QUEX_NAME(BufferFiller)*)0x0;
        }
    } 

    return QUEX_NAME(BufferFiller_new)(byte_loader, converter,
                                       QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}

QUEX_INLINE void       
QUEX_NAME(BufferFiller_delete)(QUEX_NAME(BufferFiller)** me)
{ 
    if     ( ! *me )                                           return;
    else if( (*me)->ownership != E_Ownership_LEXICAL_ANALYZER) return;
    else if( (*me)->delete_self )                              (*me)->delete_self(*me);
    (*me) = (QUEX_NAME(BufferFiller)*)0;
}

QUEX_INLINE void    
QUEX_NAME(BufferFiller_setup)(QUEX_NAME(BufferFiller)*   me,
                              size_t       (*derived_input_character_load)(QUEX_NAME(BufferFiller)*,
                                                                           QUEX_TYPE_CHARACTER*, const size_t),
                              ptrdiff_t    (*stomach_byte_n)(QUEX_NAME(BufferFiller)*),
                              void         (*stomach_clear)(QUEX_NAME(BufferFiller)*),
                              void         (*derived_delete_self)(QUEX_NAME(BufferFiller)*),
                              void         (*derived_fill_prepare)(QUEX_NAME(Buffer)*  me,
                                                                   void**              begin_p,
                                                                   const void**        end_p),
                              ptrdiff_t    (*derived_fill_finish)(QUEX_NAME(BufferFiller)*   me,
                                                                  QUEX_TYPE_CHARACTER*       BeginP,
                                                                  const QUEX_TYPE_CHARACTER* EndP,
                                                                  const void*                FilledEndP),
                              ByteLoader*  byte_loader,
                              ptrdiff_t    ByteNPerCharacter)
{
    __quex_assert(me);
    __quex_assert(derived_input_character_load);
    __quex_assert(derived_delete_self);

    /* Support for buffer filling without user interaction                   */
    me->stomach_byte_n               = stomach_byte_n;
    me->stomach_clear                = stomach_clear;
    me->input_character_tell         = QUEX_NAME(BufferFiller_character_index_tell);
    me->input_character_seek         = QUEX_NAME(BufferFiller_character_index_seek);
    me->derived_input_character_load = derived_input_character_load;
    me->delete_self                  = derived_delete_self;
    me->_on_overflow                 = 0x0;

    /* Support for manual buffer filling.                                    */
    me->fill                 = QUEX_NAME(BufferFiller_fill);

    me->fill_prepare         = QUEX_NAME(BufferFiller_fill_prepare);
    me->fill_finish          = QUEX_NAME(BufferFiller_fill_finish);
    me->derived_fill_prepare = derived_fill_prepare;
    me->derived_fill_finish  = derived_fill_finish;

    me->byte_loader                    = byte_loader;

    me->_byte_order_reversion_active_f = false;
    me->character_index_next_to_fill   = 0;
    me->byte_n_per_character           = ByteNPerCharacter;

    /* Default: External ownership                                           */
    me->ownership = E_Ownership_EXTERNAL;
}

QUEX_INLINE void
QUEX_NAME(BufferFiller_reset)(QUEX_NAME(BufferFiller)* me, ByteLoader* new_byte_loader)
/* Resets the BufferFiller with a new ByteLoader.                            */
{
    __quex_assert(new_byte_loader);

    if( new_byte_loader != me->byte_loader ) {
        if( ByteLoader_is_equivalent(new_byte_loader, me->byte_loader) ) {
            /* QUEX_ERROR_EXIT("Upon 'reset': current and new ByteLoader objects contain same input handle."); */
        }
        else {
            ByteLoader_delete(&me->byte_loader);
            me->byte_loader = new_byte_loader;
        }
    }
    QUEX_NAME(BufferFiller_character_index_reset)(me);
}

QUEX_INLINE ptrdiff_t       
QUEX_NAME(BufferFiller_load)(QUEX_NAME(BufferFiller)*  me, 
                             QUEX_TYPE_CHARACTER*      LoadP, 
                             const ptrdiff_t           LoadN,
                             QUEX_TYPE_STREAM_POSITION StartCharacterIndex)
/* Seeks the input position StartCharacterIndex and loads 'LoadN' 
 * characters into the engine's buffer starting from 'LoadP'.
 *
 * RETURNS: Number of loaded characters.                                     */
{
    ptrdiff_t   loaded_n;

    /* (1) Seek to the position where loading shall start.                       
     *                                                                       */
    if( ! me->input_character_seek(me, StartCharacterIndex) ) {
        return 0;
    }
    __quex_assert(me->character_index_next_to_fill == StartCharacterIndex);

    /* (2) Load content into the given region.                                   
     *                                                                       */
    loaded_n = (ptrdiff_t)me->derived_input_character_load(me, LoadP, (size_t)LoadN);
    __quex_assert(loaded_n <= LoadN);

    if(    me->character_index_next_to_fill - StartCharacterIndex 
        != (QUEX_TYPE_STREAM_POSITION)loaded_n ) {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM); 
    }

    /* (3) Optionally reverse the byte order.                                    
     *                                                                       */
    if( me->_byte_order_reversion_active_f ) {
        QUEX_NAME(Buffer_reverse_byte_order)(LoadP, &LoadP[loaded_n]);
    }

    return loaded_n;
}

QUEX_INLINE void*
QUEX_NAME(BufferFiller_fill)(QUEX_NAME(Buffer)*  buffer, 
                             const void*         ContentBegin,
                             const void*         ContentEnd)
{
    ptrdiff_t      copy_n;
    void*          begin_p;
    const void*    end_p;

    /* Prepare the buffer for the reception of new input an acquire the
     * border pointers of where new content can be filled.                   */
    buffer->filler->fill_prepare(buffer, &begin_p, &end_p);

    /* Copy as much as possible of the new content into the designated
     * region in memory. This may be the engine's buffer or a 'raw' buffer
     * whose content still needs to be converted.                            */
    copy_n = (ptrdiff_t)QUEXED(MemoryManager_insert)((uint8_t*)begin_p,  
                                                     (uint8_t*)end_p,
                                                     (uint8_t*)ContentBegin, 
                                                     (uint8_t*)ContentEnd);

    /* Flush into buffer what has been filled from &begin[0] to 
     * &begin[inserted_byte_n].                                              */
    buffer->filler->fill_finish(buffer, &((uint8_t*)begin_p)[copy_n]);

    /* Report a pointer to the first content element that has not yet 
     * been treated (== ContentEnd if all complete).                         */
    return (void*)&((uint8_t*)ContentBegin)[copy_n];
}

QUEX_INLINE void
QUEX_NAME(BufferFiller_fill_prepare)(QUEX_NAME(Buffer)*  buffer, 
                                     void**              begin_p, 
                                     const void**        end_p)
/* SETS: *begin_p: position where the next content needs to be filled. 
 *       *end_p:   address directly behind the last byte that can be filled.
 *
 * The content may be filled into the engine's buffer or an intermediate 
 * 'raw' buffer which still needs to be converted.                          */
{
    (void)QUEX_NAME(Buffer_move_away_passed_content)(buffer);

    /* Get the pointers for the border where to fill content.               */
    buffer->filler->derived_fill_prepare(buffer, begin_p, end_p);

    __quex_assert(*end_p >= *begin_p);
}

QUEX_INLINE void
QUEX_NAME(BufferFiller_fill_finish)(QUEX_NAME(Buffer)* buffer,
                                    const void*        FilledEndP)
{
    ptrdiff_t  inserted_character_n;

    /* Place new content in the engine's buffer.                             */
    inserted_character_n = buffer->filler->derived_fill_finish(buffer->filler, 
                                                               buffer->input.end_p,
                                                               buffer->_memory._back, 
                                                               FilledEndP);

    /* Assume: content from 'input.end_p' to 'input.end_p[CharN]'
     * has been filled with data.                                            */
    if( buffer->filler->_byte_order_reversion_active_f ) {
        QUEX_NAME(Buffer_reverse_byte_order)(buffer->input.end_p, 
                                             &buffer->input.end_p[inserted_character_n]);
    }

    /* When lexing directly on the buffer, the end of file pointer is 
     * always set.                                                           */
    QUEX_NAME(Buffer_register_content)(buffer, 
                                       &buffer->input.end_p[inserted_character_n],
                                       buffer->input.character_index_begin + inserted_character_n); 

    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/buffer/filler/BufferFiller_navigation.i>
#include <quex/code_base/buffer/filler/BufferFiller_Converter.i>
#include <quex/code_base/buffer/filler/BufferFiller_Plain.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

