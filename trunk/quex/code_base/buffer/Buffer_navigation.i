#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I
/* PURPOSE: Buffer's seek: 
 * 
 *       Setting the '_read_p' to a specific position in the stream.
 *
 * This is the type of 'seek' used in the user interface's seek functions.
 *
 * NOT TO CONFUSE with two other forms of seek:
 *
 *    -- BufferFiller's seek sets the input position of the next 
 *       character to be loaded into the buffer.
 *    -- ByteLoader's seek sets the position in the low level input
 *       stream.
 *
 * A 'seek' always implies that the following happens:
 *
 *                      _lexeme_start_p = _read_p  
 * 
 * The two stored characters will be assigned after seeking as
 *
 *       _character_at_lexeme_start     = _read_p[0]
 *       _character_before_lexeme_start = _read_p[-1]
 * 
 * If the read pointer stands at the beginning of the file, then
 *
 *       _character_before_lexeme_start = newline
 *
 * It is crucial to understand the difference between 'stream seeking' and 
 * 'buffer seeking'. Stream seeking determines the next position in the input
 * stream from where content is loaded into the buffer. Buffer seeking sets
 * the input pointer '_read_p' to a particular position. The position-1 where 
 * it points contains the next character to be read during analysis.           
 *
 * (C) Frank-Rene Schaefer                                                   */

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE bool
QUEX_NAME(Buffer_finish_seek_based_on_read_p)(QUEX_NAME(Buffer)* me);

QUEX_INLINE QUEX_TYPE_CHARACTER*
QUEX_NAME(Buffer_tell_memory_adr)(QUEX_NAME(Buffer)* buffer)
{

    /* NOT: QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);                          
     *
     * This function is used by the range skippers, and they write possibly
     * something on the end of file pointer, that is different from the buffer
     * limit code.                                                           */
    return (QUEX_TYPE_CHARACTER*)(buffer->_read_p);
}

QUEX_INLINE void
QUEX_NAME(Buffer_seek_memory_adr)(QUEX_NAME(Buffer)* buffer, QUEX_TYPE_CHARACTER* Position)
{
    buffer->_read_p = Position;
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_seek_forward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_read_p' forwards by 'CharacterN'. This may involve reload in 
 * forward direction. 
 *
 * Seeking error => Buffer is completely left as is. In particular no change
 *                  to '_read_p' or '_lexeme_start_p'. 
 * 
 * RETURNS: True -- if positioning was successful,
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER*       BeginP = &me->_memory._front[1];
    QUEX_TYPE_STREAM_POSITION  CharacterIndexAtBegin = QUEX_NAME(Buffer_input_begin_character_index)(me);
    QUEX_TYPE_STREAM_POSITION  CharacterIndexAtReadP =   CharacterIndexAtBegin
                                                       + (me->_read_p - BeginP);
    ptrdiff_t                  target = CharacterIndexAtReadP + CharacterN;
    QUEX_TYPE_STREAM_POSITION  new_character_index_begin;

    if( ! CharacterN ) {
        return true;
    }
    else if( target < me->input.end_character_index ) {
        me->_read_p += CharacterN;
        /* => &me->_read_p[-1] inside buffer.                                */
    }
    else if( me->input.end_p ) {
        return false;
    }
    else {
        /* Character index at read_p = character index at begin + offset     */
        new_character_index_begin = QUEX_MAX(0, target - QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        if( ! QUEX_NAME(Buffer_move_and_fill_forward)(me, new_character_index_begin) ) {
            return false;
        }

        me->_read_p = &BeginP[target - new_character_index_begin];
    }
    me->_lexeme_start_p = me->_read_p;

    return QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_seek_backward)(QUEX_NAME(Buffer)* me, 
                                const ptrdiff_t    CharacterN)
/* Move '_read_p' backwards by 'CharacterN'. This may involve reload in
 * backward direction.                                                   
 *
 * Seeking error => Buffer is completely left as is. In particular no change
 *                  to '_read_p' or '_lexeme_start_p'. 
 * 
 * RETURNS: True -- if positioning was successful, 
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER*       BeginP = &me->_memory._front[1];
    QUEX_TYPE_STREAM_POSITION  CharacterIndexAtBegin = QUEX_NAME(Buffer_input_begin_character_index)(me);
    QUEX_TYPE_STREAM_POSITION  CharacterIndexAtReadP =   CharacterIndexAtBegin
                                                       + (me->_read_p - BeginP);
    ptrdiff_t                  target = CharacterIndexAtReadP - CharacterN;
    const size_t               ContentSize = QUEX_NAME(Buffer_content_size)(me); 
    QUEX_TYPE_STREAM_POSITION  new_character_index_begin;
    ptrdiff_t                  offset;

    if( ! CharacterN ) {
        return true;
    }
    else if( target > CharacterIndexAtBegin ) {
        /* => &me->_read_p[-1] inside buffer.                                */
        me->_read_p -= CharacterN;
    }
    else {
        /* offset = desired distance from begin to 'read_p'.                 */
        offset                    = QUEX_MIN((ContentSize >> 1), target);
        new_character_index_begin = target - offset;

        if( ! QUEX_NAME(Buffer_move_and_fill_backward)(me, new_character_index_begin) ) 
            return false;
        me->_read_p = &BeginP[offset];
    }

    return QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_tell)(QUEX_NAME(Buffer)* me)
/* RETURNS: character index which corresponds to the position of the input
 *          pointer.                                                         */
{
    const QUEX_TYPE_STREAM_POSITION DeltaToBufferBegin = me->_read_p - &me->_memory._front[1];
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    return DeltaToBufferBegin + QUEX_NAME(Buffer_input_begin_character_index)(me);
}

QUEX_INLINE void    
QUEX_NAME(Buffer_seek)(QUEX_NAME(Buffer)* me, const QUEX_TYPE_STREAM_POSITION CharacterIndex)
/* Set the _read_p according to a character index of the input. It is the 
 * inverse of 'tell()'.                                                      */
{
    const QUEX_TYPE_STREAM_POSITION CurrentCharacterIndex = QUEX_NAME(Buffer_tell)(me);

    if( CharacterIndex > CurrentCharacterIndex ) {
        QUEX_NAME(Buffer_seek_forward)(me, (ptrdiff_t)(CharacterIndex - CurrentCharacterIndex));
    }
    else if( CharacterIndex < CurrentCharacterIndex ) {
        QUEX_NAME(Buffer_seek_backward)(me,(ptrdiff_t)(CurrentCharacterIndex - CharacterIndex));
    }
}

QUEX_INLINE bool
QUEX_NAME(Buffer_finish_seek_based_on_read_p)(QUEX_NAME(Buffer)* me)
{
    QUEX_TYPE_CHARACTER* BeginP    = &me->_memory._front[1];
    bool                 verdict_f = true;

    if( me->_read_p >= QUEX_NAME(Buffer_text_end)(me) ) {
        me->_read_p = QUEX_NAME(Buffer_text_end)(me);
        verdict_f = false;
    }
    else if( me->_read_p < BeginP ) {
        me->_read_p = BeginP;
        verdict_f = false;
    }

    me->_lexeme_start_p                = me->_read_p;
    me->_character_at_lexeme_start     = me->_read_p[0];
#   ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    /* Seek was towards 'target - 1'
     * => Now, there must be at least one character before '_read_p'.
     *    Or if not, then the target was on the lower limit 0 and the '_read_p'
     *    stands on the buffer's content front.                              */
    me->_character_before_lexeme_start = me->_read_p > BeginP ? me->_read_p[-1]
                                         : QUEX_SETTING_CHARACTER_NEWLINE_IN_ENGINE_CODEC;
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return verdict_f;
}

QUEX_NAMESPACE_MAIN_CLOSE
#endif                  /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I */
