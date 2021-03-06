/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__LEXATOM_LOADER_I
#define  __QUEX_INCLUDE_GUARD__BUFFER__LEXATOMS__LEXATOM_LOADER_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/lexatoms/LexatomLoader>
#include <quex/code_base/buffer/Buffer_debug>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE bool       QUEX_NAME(LexatomLoader_lexatom_index_seek)(QUEX_NAME(LexatomLoader)*         me, 
                                                                    const QUEX_TYPE_STREAM_POSITION  LexatomIndex);
QUEX_INLINE QUEX_TYPE_STREAM_POSITION 
                       QUEX_NAME(LexatomLoader_lexatom_index_tell)(QUEX_NAME(LexatomLoader)* me);
QUEX_INLINE bool       QUEX_NAME(LexatomLoader_lexatom_index_step_to)(QUEX_NAME(LexatomLoader)*        me,
                                                                       const QUEX_TYPE_STREAM_POSITION TargetCI);
QUEX_INLINE void       QUEX_NAME(LexatomLoader_lexatom_index_reset_backup)(QUEX_NAME(LexatomLoader)* me, 
                                                          QUEX_TYPE_STREAM_POSITION Backup_lexatom_index_next_to_fill, 
                                                          ptrdiff_t                 BackupStomachByteN, 
                                                          QUEX_TYPE_STREAM_POSITION BackupByteLoaderPosition);
QUEX_INLINE void       QUEX_NAME(LexatomLoader_reverse_byte_order)(QUEX_TYPE_LEXATOM*       Begin, 
                                                                  const QUEX_TYPE_LEXATOM* End);

QUEX_INLINE void       QUEX_NAME(LexatomLoader_delete_self)(QUEX_NAME(LexatomLoader)*); 

                       
QUEX_INLINE QUEX_NAME(LexatomLoader)*
QUEX_NAME(LexatomLoader_new)(QUEX_NAME(ByteLoader)*  byte_loader, 
                            QUEX_NAME(Converter)*   converter,
                            const size_t            TranslationBufferMemorySize)
{
    QUEX_NAME(LexatomLoader)* filler;
    (void)TranslationBufferMemorySize;

    /* byte_loader = 0; possible if memory is filled manually.               */
    if( converter ) {
        filler = QUEX_NAME(LexatomLoader_Converter_new)(byte_loader, converter, 
                                                       TranslationBufferMemorySize);
    }
    else {
        filler = QUEX_NAME(LexatomLoader_Plain_new)(byte_loader); 
    }
    
    return filler;
}

QUEX_INLINE QUEX_NAME(LexatomLoader)* 
QUEX_NAME(LexatomLoader_new_DEFAULT)(QUEX_NAME(ByteLoader)*   byte_loader, 
                                    const char*              InputCodecName) 
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
            return (QUEX_NAME(LexatomLoader)*)0x0;
        }
    } 

    return QUEX_NAME(LexatomLoader_new)(byte_loader, converter,
                                       QUEX_SETTING_TRANSLATION_BUFFER_SIZE);
}

QUEX_INLINE void       
QUEX_NAME(LexatomLoader_delete_self)(QUEX_NAME(LexatomLoader)* me)
{ 
    if( ! me ) return;

    if( me->byte_loader && me->byte_loader->ownership == E_Ownership_LEXICAL_ANALYZER ) {
        QUEX_NAME(ByteLoader_delete)(&me->byte_loader);
    }

    /* destruct_self: Free resources occupied by 'me' BUT NOT 'myself'.
     * delete_self:   Free resources occupied by 'me' AND 'myself'.          */
    if( me->derived.destruct_self ) {
        me->derived.destruct_self(me);
    }

    QUEXED(MemoryManager_free)((void*)me, E_MemoryObjectType_BUFFER_FILLER);
}

QUEX_INLINE void    
QUEX_NAME(LexatomLoader_setup)(QUEX_NAME(LexatomLoader)*   me,
                               size_t       (*derived_load_lexatoms)(QUEX_NAME(LexatomLoader)*,
                                                                     QUEX_TYPE_LEXATOM*, 
                                                                     const size_t, 
                                                                     bool*, bool*),
                               ptrdiff_t    (*stomach_byte_n)(QUEX_NAME(LexatomLoader)*),
                               void         (*stomach_clear)(QUEX_NAME(LexatomLoader)*),
                               void         (*derived_destruct_self)(QUEX_NAME(LexatomLoader)*),
                               void         (*derived_fill_prepare)(QUEX_NAME(LexatomLoader)*  me,
                                                                    QUEX_TYPE_LEXATOM*      RegionBeginP,
                                                                    QUEX_TYPE_LEXATOM*      RegionEndP,
                                                                    void**                    begin_p,
                                                                    const void**              end_p),
                               ptrdiff_t    (*derived_fill_finish)(QUEX_NAME(LexatomLoader)*   me,
                                                                   QUEX_TYPE_LEXATOM*       BeginP,
                                                                   const QUEX_TYPE_LEXATOM* EndP,
                                                                   const void*                FilledEndP),
                               QUEX_NAME(ByteLoader)*  byte_loader,
                               ptrdiff_t    ByteNPerCharacter)
{
    __quex_assert(me);
    __quex_assert(derived_load_lexatoms);
    __quex_assert(derived_destruct_self);

    /* Support for buffer filling without user interaction                   */
    me->stomach_byte_n        = stomach_byte_n;
    me->stomach_clear         = stomach_clear;
    me->input_lexatom_tell    = QUEX_NAME(LexatomLoader_lexatom_index_tell);
    me->input_lexatom_seek    = QUEX_NAME(LexatomLoader_lexatom_index_seek);
    me->derived.load_lexatoms = derived_load_lexatoms;
    me->derived.destruct_self = derived_destruct_self;
    me->delete_self           = QUEX_NAME(LexatomLoader_delete_self);

    /* Support for manual buffer filling.                                    */
    me->derived.fill_prepare    = derived_fill_prepare;
    me->derived.fill_finish     = derived_fill_finish;

    me->byte_loader                    = byte_loader;

    me->_byte_order_reversion_active_f = false;
    me->lexatom_index_next_to_fill   = 0;
    me->byte_n_per_lexatom           = ByteNPerCharacter;

    /* Default: External ownership                                           */
    me->ownership = E_Ownership_EXTERNAL;
}

QUEX_INLINE void
QUEX_NAME(LexatomLoader_reset)(QUEX_NAME(LexatomLoader)* me, QUEX_NAME(ByteLoader)* new_byte_loader)
/* Resets the LexatomLoader with a new QUEX_NAME(ByteLoader).                            */
{
    __quex_assert(new_byte_loader);

    if( new_byte_loader != me->byte_loader ) {
        if( QUEX_NAME(ByteLoader_is_equivalent)(new_byte_loader, me->byte_loader) ) {
            __QUEX_STD_printf("Upon 'reset': current and new QUEX_NAME(ByteLoader )objects contain same input handle.\n"); 
        }
        QUEX_NAME(ByteLoader_delete)(&me->byte_loader);
        me->byte_loader = new_byte_loader;
    }
    QUEX_NAME(LexatomLoader_lexatom_index_reset)(me);
}

QUEX_INLINE ptrdiff_t       
QUEX_NAME(LexatomLoader_load)(QUEX_NAME(LexatomLoader)*  me, 
                              QUEX_TYPE_LEXATOM*         LoadP, 
                              const ptrdiff_t            LoadN,
                              QUEX_TYPE_STREAM_POSITION  StartLexatomIndex,
                              bool*                      end_of_stream_f,
                              bool*                      encoding_error_f)
/* Seeks the input position StartLexatomIndex and loads 'LoadN' 
 * lexatoms into the engine's buffer starting from 'LoadP'.
 *
 * RETURNS: Number of loaded lexatoms.                                     */
{
    ptrdiff_t   loaded_n;

    /* (1) Seek to the position where loading shall start.                       
     *                                                                       */
    if( ! me->input_lexatom_seek(me, StartLexatomIndex) ) {
        return 0;
    }
    __quex_assert(me->lexatom_index_next_to_fill == StartLexatomIndex);

    /* (2) Load content into the given region.                                   
     *                                                                       */
    loaded_n = (ptrdiff_t)me->derived.load_lexatoms(me, LoadP, (size_t)LoadN,
                                                    end_of_stream_f, encoding_error_f);
    __quex_assert(loaded_n <= LoadN);
    me->lexatom_index_next_to_fill += loaded_n;

    /* (3) Optionally reverse the byte order.                                    
     *                                                                       */
    if( me->_byte_order_reversion_active_f ) {
        QUEX_NAME(LexatomLoader_reverse_byte_order)(LoadP, &LoadP[loaded_n]);
    }

    return loaded_n;
}


QUEX_INLINE void
QUEX_NAME(LexatomLoader_reverse_byte_order)(QUEX_TYPE_LEXATOM*       Begin, 
                                           const QUEX_TYPE_LEXATOM* End)
{
    uint8_t              tmp = 0xFF;
    QUEX_TYPE_LEXATOM* iterator = 0x0;

    switch( sizeof(QUEX_TYPE_LEXATOM) ) {
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

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/bytes/ByteLoader.i>
#include <quex/code_base/buffer/lexatoms/LexatomLoader_navigation.i>
#include <quex/code_base/buffer/lexatoms/LexatomLoader_Converter.i>
#include <quex/code_base/buffer/lexatoms/LexatomLoader_Plain.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

