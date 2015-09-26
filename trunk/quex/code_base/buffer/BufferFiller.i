/* -*- C++ -*- vim: set syntax=cpp: */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_FILLER_I

#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/Buffer_debug>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void*      QUEX_NAME(BufferFiller_fill)(QUEX_NAME(Buffer)* buffer, 
                                                    const void*        ContentBegin, 
                                                    const void*        ContentEnd);
QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_prepare)(QUEX_NAME(Buffer)*  buffer, 
                                                            void**              begin_p, 
                                                            const void**        end_p);
QUEX_INLINE void       QUEX_NAME(BufferFiller_fill_finish)(QUEX_NAME(Buffer)* buffer,
                                                           const void*        FilledEndP);
QUEX_INLINE void       QUEX_NAME(__BufferFiller_on_overflow)(QUEX_NAME(Buffer)*, bool ForwardF);
                       
QUEX_INLINE ptrdiff_t  QUEX_NAME(__BufferFiller_input_character_read)(QUEX_NAME(BufferFiller)*, 
                                                                      QUEX_TYPE_CHARACTER*, 
                                                                      const ptrdiff_t,
                                                                      QUEX_TYPE_STREAM_POSITION);

QUEX_INLINE QUEX_NAME(BufferFiller)*
QUEX_NAME(BufferFiller_new)(ByteLoader*           byte_loader, 
                            QUEX_NAME(Converter)* converter,
                            const char*           CharacterEncodingName,
                            const size_t          TranslationBufferMemorySize)
/* CharacterEncoding == 0x0: Impossible; Converter requires codec name 
 *                           --> filler = 0x0
 * input_handle      == 0x0: Possible; Converter might be applied on buffer. 
 *                           (User writes into translation buffer).          */
{
    QUEX_NAME(BufferFiller)* filler;
    (void)TranslationBufferMemorySize;

#   if    defined(QUEX_OPTION_CONVERTER_ICONV) \
       || defined(QUEX_OPTION_CONVERTER_ICU) 
    if( ! CharacterEncodingName ) {
#   ifndef QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED
        __QUEX_STD_printf("Warning: No character encoding name specified, while this\n" \
                          "Warning: analyzer was generated for use with a converter.\n" \
                          "Warning: Please, consult the documentation about the constructor\n" \
                          "Warning: or the reset function. If it is desired to do a plain\n" \
                          "Warning: buffer filler with this setup, you might want to disable\n" \
                          "Warning: this warning with the macro:\n" \
                          "Warning:     QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED\n");
#   endif
        return (QUEX_NAME(BufferFiller*))0x0;
    } 
#   endif

    /* byte_loader = 0; possible if memory is filled manually.               */
    if( converter ) {
        filler = QUEX_NAME(BufferFiller_Converter_new)(byte_loader,
                                                       converter, 
                                                       CharacterEncodingName, 
                                                       /* Default Codec */0x0,
                                                       TranslationBufferMemorySize);
    }
    else {
        filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader); 
    }
    
    return filler;
}

QUEX_INLINE QUEX_NAME(BufferFiller)* 
QUEX_NAME(BufferFiller_DEFAULT)(ByteLoader*   byte_loader, 
                                const char*   CharacterEncodingName) 
{
#   if   defined(QUEX_OPTION_CONVERTER_ICU)
    QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_ICU_new)();
#   elif defined(QUEX_OPTION_CONVERTER_ICONV)
    QUEX_NAME(Converter)* converter = QUEX_NAME(Converter_IConv_new)();
#   else
    QUEX_NAME(Converter)* converter = (QUEX_NAME(Converter)*)0;
#   endif
    if( converter ) {
        converter->ownership = E_Ownership_LEXICAL_ANALYZER;
    }
    return QUEX_NAME(BufferFiller_new)(byte_loader, converter,
                                       CharacterEncodingName, 
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
                              QUEX_TYPE_STREAM_POSITION    
                                           (*derived_input_character_tell)(QUEX_NAME(BufferFiller)*),
                              void         (*derived_input_character_seek)(QUEX_NAME(BufferFiller)*, 
                                                                           const QUEX_TYPE_STREAM_POSITION),
                              size_t       (*derived_input_character_read)(QUEX_NAME(BufferFiller)*,
                                                                           QUEX_TYPE_CHARACTER*, const size_t),
                              void         (*derived_delete_self)(QUEX_NAME(BufferFiller)*),
                              void         (*derived_fill_prepare)(QUEX_NAME(Buffer)*  me,
                                                                   void**              begin_p,
                                                                   const void**        end_p),
                              ptrdiff_t    (*derived_fill_finish)(QUEX_NAME(BufferFiller)*   me,
                                                                  QUEX_TYPE_CHARACTER*       BeginP,
                                                                  const QUEX_TYPE_CHARACTER* EndP,
                                                                  const void*                FilledEndP),
                              ByteLoader*  byte_loader)
{
    __quex_assert(me);
    __quex_assert(derived_input_character_seek);
    __quex_assert(derived_input_character_seek);
    __quex_assert(derived_input_character_read);
    __quex_assert(derived_delete_self);

    /* Support for buffer filling without user interaction                   */
    me->derived_input_character_tell = derived_input_character_tell;
    me->derived_input_character_seek = derived_input_character_seek;
    me->derived_input_character_read = derived_input_character_read;
    me->delete_self                  = derived_delete_self;
    me->_on_overflow                 = 0x0;

    /* Support for manual buffer filling.                                    */
    me->fill                 = QUEX_NAME(BufferFiller_fill);

    me->fill_prepare         = QUEX_NAME(BufferFiller_fill_prepare);
    me->fill_finish          = QUEX_NAME(BufferFiller_fill_finish);
    me->derived_fill_prepare = derived_fill_prepare;
    me->derived_fill_finish  = derived_fill_finish;

    me->byte_loader          = byte_loader;

    me->_byte_order_reversion_active_f = false;

    /* Default: External ownership                                           */
    me->ownership = E_Ownership_EXTERNAL;
}

QUEX_INLINE void
QUEX_NAME(BufferFiller_reset)(QUEX_NAME(BufferFiller)* me, ByteLoader* new_byte_loader)
{
    __quex_assert(new_byte_loader);

    if( new_byte_loader == me->byte_loader ) {
        /* Nothing to be done.                                               */
    }
    else if( ByteLoader_compare(new_byte_loader, me->byte_loader) ) {
        QUEX_ERROR_EXIT("Upon 'reset': current and new ByteLoader objects contain same input handle.");
    }
    else {
        ByteLoader_delete(&me->byte_loader);
        me->byte_loader = new_byte_loader;
    }

    me->byte_loader->seek(me->byte_loader, (QUEX_TYPE_STREAM_POSITION)0);
}

QUEX_INLINE size_t
QUEX_NAME(BufferFiller_load_forward)(QUEX_NAME(Buffer)* buffer)
/* Load as much new content into the buffer as possible--from what lies
 * ahead in the input stream. The '_read_p' and the '_lexeme_start_p' 
 * MUST be maintained inside the buffer. The 'input.end_p' pointer
 * and 'input.end_character_index' are adapted according to the newly
 * loaded content.
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_TYPE_CHARACTER*        BeginP      = &buffer->_memory._front[1];
    QUEX_TYPE_CHARACTER*        EndP        = buffer->_memory._back;
    const ptrdiff_t             ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
    ptrdiff_t                   required_load_n;
    ptrdiff_t                   loaded_n;
    QUEX_TYPE_CHARACTER*        free_begin_p;
    QUEX_TYPE_STREAM_POSITION   end_character_index;
    QUEX_TYPE_CHARACTER*        end_p;
    QUEX_NAME(BufferFiller)*    me;

    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

    __quex_debug_buffer_load(buffer, "FORWARD(entry)\n");

    me = buffer->filler;
    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = Beginning of the Buffer: Reload nonsense. Maximum 
     *    size of available content lies ahead of '_read_p'.
     * -- input.end_p != 0: Tail of file read is already in buffer.          */
    if( ! me ) return 0;             /* Possible, if no filler specified     */    
    else if( buffer->_read_p - buffer->_lexeme_start_p >= ContentSize ) { 
        /* OVERFLOW: If stretch from _read_p to _lexeme_start_p 
         * spans the whole buffer, then nothing can be loaded.               */
        QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ true);
        return 0;
    }
    else if( QUEX_NAME(Buffer_is_empty)(buffer) ) { 
        /* Load the whole buffer.                                            */
        free_begin_p = BeginP;
    }
    else {
        /* Move old content that has to remain (also, fall back region).
         * (Maintains '_read_p' and '_lexeme_start_p' inside the buffer)     */
        free_begin_p = QUEX_NAME(Buffer_move_away_passed_content)(buffer);
        if( ! free_begin_p ) return 0; 
    }
    required_load_n = EndP - free_begin_p;

    /* Load new content                                                      */
    loaded_n = QUEX_NAME(__BufferFiller_input_character_read)(buffer->filler, 
                                                              free_begin_p, 
                                                              required_load_n,
                                                              buffer->input.end_character_index);
    __quex_assert(loaded_n <= required_load_n);

    /* input.end_p, input.end_character_index
     *                                                                       */
    end_p = (EndP - free_begin_p == loaded_n) ? (QUEX_TYPE_CHARACTER*)0
                                               : &free_begin_p[loaded_n];
    end_character_index = buffer->input.end_character_index + loaded_n;
    QUEX_NAME(Buffer_input_end_set)(buffer, end_p, end_character_index);
    
    __quex_debug_buffer_load(buffer, "LOAD FORWARD(exit)\n");

    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    return (size_t)loaded_n; 
}

QUEX_INLINE size_t   
QUEX_NAME(BufferFiller_load_backward)(QUEX_NAME(Buffer)* buffer)
/* Load *previous* content into the buffer so that the analyzer can 
 * continue seeminglessly (in backward direction).
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_NAME(BufferFiller)*   me = buffer->filler;
    QUEX_TYPE_CHARACTER*       BeginP = &buffer->_memory._front[1];
    QUEX_TYPE_CHARACTER*       EndP   = buffer->_memory._back;
    ptrdiff_t                  free_size;
    QUEX_TYPE_STREAM_POSITION  load_begin_character_index;

#   ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
    QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM_IN_BACKWARD_LOAD);
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

    __quex_debug_buffer_load(buffer, "BACKWARD(entry)\n");

    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = End of the Buffer: Reload nonsense. Maximum size of
     *    available content lies before of '_read_p' for backward lexing..
     * -- input.end_character_index == 0: Stading at begin, already.         */
    if( ! me ) return 0;             /* Possible, if no filler specified     */    
    else if( buffer->_lexeme_start_p >= &EndP[-1] ) { 
        /* If _lexeme_start_p at back, then no new content can be loaded.    */
        QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ false);
        return 0;
    }
    else if( QUEX_NAME(Buffer_is_empty)(buffer) ) { 
        /* Load the whole buffer.                                            */
        free_size                  = EndP - BeginP;
        load_begin_character_index = (QUEX_TYPE_STREAM_POSITION)0;
    }
    else {
        /* Move old content that has to remain. The analyzer soon will have to 
         * go forward again, so some content better remains.                 */
        free_size = QUEX_NAME(Buffer_move_away_upfront_content)(buffer); 
        if( ! free_size ) return 0;
        load_begin_character_index =   buffer->input.end_character_index
                                     - (QUEX_NAME(Buffer_text_end)(buffer) - BeginP);
        __quex_assert(load_begin_character_index >= 0);
    }

    /* Load new content                                                      */
    (void)QUEX_NAME(__BufferFiller_input_character_read)(buffer->filler, 
                                                         BeginP, 
                                                         free_size,
                                                         load_begin_character_index);

    __quex_debug_buffer_load(buffer, "BACKWARD(exit)\n");
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    return (size_t)free_size;
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
     * region in memory.                                                     */
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
/* RETURNS: The position of the first character that could not be copied
 *          into the fill region, because it did not have enough space.
 *          If the whole content was copied, then the return value
 *          is equal to BufferEnd.                                           */
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
                                                               QUEX_NAME(Buffer_text_end)(buffer),
                                                               &QUEX_NAME(Buffer_content_back)(buffer)[1], 
                                                               FilledEndP);

    /* Assume: content from 'input.end_p' to 'input.end_p[CharN]'
     * has been filled with data.                                            */
    if( buffer->filler->_byte_order_reversion_active_f ) {
        QUEX_NAME(Buffer_reverse_byte_order)(buffer->input.end_p, 
                                             &buffer->input.end_p[inserted_character_n]);
    }

    /* When lexing directly on the buffer, the end of file pointer is 
     * always set.                                                           */
    QUEX_NAME(Buffer_input_end_set)(buffer, 
                                    &buffer->input.end_p[inserted_character_n],
                                    buffer->input.end_character_index + inserted_character_n);

    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
}

QUEX_INLINE ptrdiff_t       
QUEX_NAME(__BufferFiller_input_character_read)(QUEX_NAME(BufferFiller)*  me, 
                                               QUEX_TYPE_CHARACTER*      memory, 
                                               const ptrdiff_t           RequiredLoadN,
                                               QUEX_TYPE_STREAM_POSITION StartCharacterIndex)
/* RETURNS: number of loaded characters.                                     */
{
    QUEX_TYPE_STREAM_POSITION  character_index_before = me->derived_input_character_tell(me);
    QUEX_TYPE_STREAM_POSITION  character_index_after;
    ptrdiff_t                  loaded_n;

    /* It is not safe to assume that the character size is fixed. Thus it
     * is up to  the input strategy to determine the input position that
     * belongs to a character  position.                                     */
    me->derived_input_character_seek(me, StartCharacterIndex);

    loaded_n = me->derived_input_character_read(me, memory, (size_t)RequiredLoadN);
    __quex_assert(loaded_n <= RequiredLoadN);

    character_index_after = me->derived_input_character_tell(me);

    if(    character_index_after - character_index_before 
        != (QUEX_TYPE_STREAM_POSITION)loaded_n ) {
        QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM); 
    }

    if( me->_byte_order_reversion_active_f ) {
        QUEX_NAME(Buffer_reverse_byte_order)(memory, &memory[loaded_n]);
    }
    return loaded_n;
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/buffer/converter/BufferFiller_Converter.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFERFILLER_I */

