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
 * RETURNS: True -- if positioning was successful,
 *          False -- else.                                                   
 *_____________________________________________________________________________
 * DETAILS:
 *
 * The function tries to seek towards the 'target - 1'. But when this position
 * is reached, then '_read_p = target + 1'. This way '_read_p - 1' lies INSIDE 
 * the buffer. It is required to determine '_character_before_lexeme_start' and
 * '_character_at_lexeme_start'. 
 *
 * Does 'read_p = target + 1' lie inside the buffer? The loading function is
 * supposed to leave content in front of the target. If not even a single 
 * character is left in front, then the seeking must be considered a failure.
 * => Check upon exit of the function and error report catches border case.  
 *    (see Buffer_finish_seek_based_on_read_p())                             */
{
    QUEX_TYPE_CHARACTER* content_back_p = &QUEX_NAME(Buffer_text_end)(me)[-1];
    ptrdiff_t            max_distance   = content_back_p - me->_read_p;
    /* Seek for 'target - 1' => delta_remaining = CharacterN + 1.            */
    ptrdiff_t            delta_remaining = CharacterN - 1;

    if( ! CharacterN ) return true;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta_remaining > max_distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        delta_remaining     -= max_distance;
        me->_read_p          = content_back_p;
        me->_lexeme_start_p  = me->_read_p;
        if( ! QUEX_NAME(BufferFiller_load_forward)(me) ) {
            return QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
        } 
        content_back_p = &QUEX_NAME(Buffer_text_end)(me)[-1];
        max_distance   = content_back_p - me->_read_p;
    }

    me->_read_p += delta_remaining + 1;                       /* see entry   */
    return QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_seek_backward)(QUEX_NAME(Buffer)* me, 
                                const ptrdiff_t    CharacterN)
/* Move '_read_p' backwards by 'CharacterN'. This may involve reload in
 * backward direction.                                                   
 * 
 * RETURNS: True -- if positioning was succesfull, 
 *          False -- else.                                                   
 *_____________________________________________________________________________
 * DETAILS:
 *
 * The function tries to seek towards the 'target - 1'. But when this position
 * is reached, then '_read_p = target + 1'. This way '_read_p - 1' lies INSIDE 
 * the buffer. It is required to determine '_character_before_lexeme_start' and
 * '_character_at_lexeme_start'. 
 *
 * Does 'read_p = target + 1' lie inside the buffer? The loading function is
 * supposed to leave content in front of the target. If not even a single 
 * character is left in front, then the seeking must be considered a failure.
 * => Check upon exit of the function and error report catches border case.  
 *    (see Buffer_finish_seek_based_on_read_p())                             */
{
    QUEX_TYPE_CHARACTER*       BeginP                 = &me->_memory._front[1];
    ptrdiff_t                  delta_to_begin         = me->_read_p - BeginP;
    QUEX_TYPE_STREAM_POSITION  read_p_character_index =   QUEX_NAME(Buffer_input_begin_character_index)(me)
                                                        + delta_to_begin; 
    ptrdiff_t                  delta_remaining;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    if( ! CharacterN ) return true;

    /* Seek for 'target - 1' => delta_remaining = CharacterN + 1.            */
    delta_remaining = CharacterN < read_p_character_index ? CharacterN + 1
                      : read_p_character_index;

    while( delta_remaining > delta_to_begin ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        delta_remaining     -= delta_to_begin;                                    
        me->_read_p          = BeginP;                               
        me->_lexeme_start_p  = me->_read_p;                             
        if( ! QUEX_NAME(BufferFiller_load_backward)(me) ) {                 
            return QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
        } 
        delta_to_begin = me->_read_p - BeginP;
    }

    me->_read_p -= delta_remaining - 1;                       /* see entry   */
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
