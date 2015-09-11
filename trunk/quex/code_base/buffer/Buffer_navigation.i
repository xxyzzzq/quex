#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE QUEX_TYPE_CHARACTER_POSITION
QUEX_NAME(Buffer_tell_memory_adr)(QUEX_NAME(Buffer)* buffer)
{
    /* NOTE: We cannot check for general consistency here, because this function 
     *       may be used by the range skippers, and they write possibly something on
     *       the end of file pointer, that is different from the buffer limit code.
     * NOT: QUEX_BUFFER_ASSERT_CONSISTENCY(buffer); */
#   if defined (QUEX_OPTION_ASSERTS) && ! defined(__QUEX_OPTION_PLAIN_C)
    return QUEX_TYPE_CHARACTER_POSITION(buffer->_input_p, QUEX_NAME(Buffer_character_index_begin)(buffer));
#   else
    return (QUEX_TYPE_CHARACTER_POSITION)(buffer->_input_p);
#   endif
}

QUEX_INLINE void
QUEX_NAME(Buffer_seek_memory_adr)(QUEX_NAME(Buffer)* buffer, QUEX_TYPE_CHARACTER_POSITION Position)
{
#   if      defined(QUEX_OPTION_ASSERTS) \
       && ! defined(__QUEX_OPTION_PLAIN_C)
    /* Check whether the memory_position is relative to the current start position   
     * of the stream. That means, that the tell_adr() command was called on the  
     * same buffer setting or the positions have been adapted using the += operator.*/
    __quex_assert(Position.buffer_start_position == (size_t)QUEX_NAME(Buffer_character_index_begin)(buffer));
    buffer->_input_p = Position.address;
#   else
    buffer->_input_p = Position;
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_character_index_begin)(QUEX_NAME(Buffer)* me)
{
    const ptrdiff_t           fill_level =   QUEX_NAME(Buffer_text_end)(me) 
                                           - &me->_memory._front[1];
    QUEX_TYPE_STREAM_POSITION result     =   me->_content_character_index_end 
                                           - fill_level;
    __quex_assert(result >= 0);
    return result;
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_move_forward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_input_p' backwards by 'CharacterN'. This may involve reload in 
 * forward direction.                                                     */
{
    QUEX_TYPE_CHARACTER* content_end    = QUEX_NAME(Buffer_text_end)(me);
    ptrdiff_t            distance       = content_end - me->_input_p;
    ptrdiff_t            delta          = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta > distance ) {
        /* _input_p + CharacterN < text_end, thus no reload necessary.    */
        delta               -= distance;
        me->_input_p         = content_end;
        me->_lexeme_start_p  = me->_input_p;
        if( ! QUEX_NAME(BufferFiller_load_forward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.           */
            me->_input_p = QUEX_NAME(Buffer_text_end)(me);  
            return false;
        } 
        content_end = QUEX_NAME(Buffer_text_end)(me);
        distance    = content_end - me->_input_p;
    }

    me->_input_p                      += delta;
    me->_lexeme_start_p                = me->_input_p;
    me->_character_at_lexeme_start     = *(me->_lexeme_start_p);
#   ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    me->_character_before_lexeme_start = *(me->_lexeme_start_p - 1);
#   endif

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return true;
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_move_backward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_input_p' backwards by 'CharacterN'. This may involve reload in 
 * backward direction.                                                   */
{
    QUEX_TYPE_CHARACTER* content_begin  = QUEX_NAME(Buffer_content_front)(me);
    ptrdiff_t            distance       = me->_input_p - content_begin;
    ptrdiff_t            delta          = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta > distance ) {
        /* _input_p + CharacterN < text_end, thus no reload necessary.    */
        delta               -= distance;
        me->_input_p         = &content_begin[-1];
        me->_lexeme_start_p  = me->_input_p - 1;
        if( ! QUEX_NAME(BufferFiller_load_backward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.           */
            me->_input_p = content_begin;
            return false;
        } 
        content_begin = QUEX_NAME(Buffer_text_end)(me);
        distance      = me->_input_p - content_begin;
    }

    me->_input_p                      -= delta;
    me->_lexeme_start_p                = me->_input_p;
    me->_character_at_lexeme_start     = *(me->_lexeme_start_p);
#   ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    me->_character_before_lexeme_start = *(me->_lexeme_start_p - 1);
#   endif

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return true;
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_tell)(QUEX_NAME(Buffer)* me)
/* RETURNS: character index which corresponds to the position of the input
 *          pointer.                                                     */
{
    const QUEX_TYPE_STREAM_POSITION DeltaToBufferBegin = me->_input_p - &me->_memory._front[1];

    return DeltaToBufferBegin + QUEX_NAME(Buffer_character_index_begin)(me);
}

QUEX_INLINE void    
QUEX_NAME(Buffer_seek)(QUEX_NAME(Buffer)* me, const QUEX_TYPE_STREAM_POSITION CharacterIndex)
/* Set the _input_p according to a character index of the input. It is the 
 * inverse of 'tell()'.                                                  */
{
    const QUEX_TYPE_STREAM_POSITION CurrentCharacterIndex = QUEX_NAME(Buffer_tell)(me);

    if( CharacterIndex > CurrentCharacterIndex ) {
        QUEX_NAME(Buffer_move_forward)(me, (ptrdiff_t)(CharacterIndex - CurrentCharacterIndex));
    }
    else {
        QUEX_NAME(Buffer_move_backward)(me,(ptrdiff_t)(CurrentCharacterIndex - CharacterIndex));
    }
}

QUEX_NAMESPACE_MAIN_CLOSE
#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I */
