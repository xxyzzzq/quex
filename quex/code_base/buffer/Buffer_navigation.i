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

QUEX_INLINE void
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
 * RETURNS: True -- if positioning was succesful,
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER* content_back_p = &QUEX_NAME(Buffer_text_end)(me)[-1];
    ptrdiff_t            max_distance   = content_back_p - me->_read_p;
    /* Seek for 'CharacterN-1' so that 'target position - 1' is in the buffer
     * and '_read_p[-1]' can be performed. Buffer sizes < 2 content characters
     * are caught be asserts.                                                */
    ptrdiff_t            delta_remaining = CharacterN - 1;

    if( ! CharacterN ) return true;
    /* Border case CharacterN = 1 <--> delta_remaining = 0:
     * => new _read_p = _read_p + 1
     * => _read_p[-1] is always inside buffer, even if _read_p at front.     */
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta_remaining > max_distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        delta_remaining     -= max_distance;
        me->_read_p          = content_back_p;
        me->_lexeme_start_p  = me->_read_p;
        if( ! QUEX_NAME(BufferFiller_load_forward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.              */
            me->_read_p = QUEX_NAME(Buffer_text_end)(me);  
            QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
            return false;
        } 
        content_back_p = &QUEX_NAME(Buffer_text_end)(me)[-1];
        max_distance   = content_back_p - me->_read_p;
    }
    me->_read_p += delta_remaining + 1;                       /* see entry   */
    QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
    return true;
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_seek_backward)(QUEX_NAME(Buffer)* me, 
                                const ptrdiff_t    CharacterN)
/* Move '_read_p' backwards by 'CharacterN'. This may involve reload in 
 * backward direction.                                                   
 * 
 * RETURNS: True -- if positioning was succesfull,
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER*       begin_p               = &me->_memory._front[1];
    ptrdiff_t                  delta_to_begin        = me->_read_p - begin_p;
    QUEX_TYPE_STREAM_POSITION  begin_character_index = QUEX_NAME(Buffer_input_begin_character_index)(me); 
    ptrdiff_t                  delta_remaining;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    if( ! CharacterN ) return true;

    if( CharacterN > begin_character_index + delta_to_begin ) {
        QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
        return false;
    }

    /* Seek for 'CharacterN+1' backwards so that 'target position - 1' is in
     * the buffer and '_read_p[-1]' can be performed. Buffer sizes < 2 content
     * characters are caught be asserts.                                     */
    delta_remaining = CharacterN + 1;

    while( delta_remaining > delta_to_begin ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        delta_remaining     -= delta_to_begin;                                    
        me->_read_p          = begin_p;                               
        me->_lexeme_start_p  = me->_read_p;                             
        if( ! QUEX_NAME(BufferFiller_load_backward)(me) ) {                 
            /* Alarm, buffer is now in some indetermined state.              */
            me->_read_p = begin_p;
            QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
            return false;
        } 
        begin_p        = QUEX_NAME(Buffer_text_end)(me);
        delta_to_begin = me->_read_p - begin_p;
    }

    me->_read_p -= delta_remaining - 1;                       /* see entry   */
    QUEX_NAME(Buffer_finish_seek_based_on_read_p)(me);
    return true;
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_tell)(QUEX_NAME(Buffer)* me)
/* RETURNS: character index which corresponds to the position of the input
 *          pointer.                                                     */
{
    const QUEX_TYPE_STREAM_POSITION DeltaToBufferBegin = me->_read_p - &me->_memory._front[1];
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    return DeltaToBufferBegin + QUEX_NAME(Buffer_input_begin_character_index)(me);
}

QUEX_INLINE void    
QUEX_NAME(Buffer_seek)(QUEX_NAME(Buffer)* me, const QUEX_TYPE_STREAM_POSITION CharacterIndex)
/* Set the _read_p according to a character index of the input. It is the 
 * inverse of 'tell()'.                                                  */
{
    const QUEX_TYPE_STREAM_POSITION CurrentCharacterIndex = QUEX_NAME(Buffer_tell)(me);

    if( CharacterIndex > CurrentCharacterIndex ) {
        QUEX_NAME(Buffer_seek_forward)(me, (ptrdiff_t)(CharacterIndex - CurrentCharacterIndex));
    }
    else if( CharacterIndex < CurrentCharacterIndex ) {
        QUEX_NAME(Buffer_seek_backward)(me,(ptrdiff_t)(CurrentCharacterIndex - CharacterIndex));
    }
}

QUEX_INLINE void 
QUEX_NAME(BufferFiller_step_forward_n_characters)(QUEX_NAME(BufferFiller)* me,
                                                  const ptrdiff_t          ForwardN)
/* STRATEGY: Starting from a certain point in the file we read characters
 *           Convert one-by-one until we reach the given character index. 
 *           This is, of course, incredibly inefficient but safe to work under
 *           all circumstances. Fillers should only rely on this function
 *           in case of no other alternative. Also, caching some information 
 *           about what character index is located at what position may help
 *           to increase speed.                                              */      
{ 
    const QUEX_TYPE_STREAM_POSITION TargetIndex =   me->derived_input_character_tell(me) 
                                                  + (QUEX_TYPE_STREAM_POSITION)ForwardN;
    /* START: Current position: 'CharacterIndex - remaining_character_n'.
     * LOOP:  It remains to interpret 'remaining_character_n' number of 
     *        characters. Since the interpretation is best done using a buffer, 
     *        we do this in chunks.                                          */ 
    size_t               remaining_character_n = (size_t)ForwardN;
    const size_t         ChunkSize             = QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE;
    QUEX_TYPE_CHARACTER  chunk[QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE];
    (void)TargetIndex;

    __quex_assert(QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE >= 1);

    /* We CANNOT assume that end the end it will hold: 
     *
     *       __quex_assert(me->derived_input_character_tell(me) == TargetIndex);
     *
     * Because, its unknown wether the stream has enough characters.         */
    for(; remaining_character_n > ChunkSize; remaining_character_n -= ChunkSize )  
        if( me->derived_input_character_read(me, (QUEX_TYPE_CHARACTER*)chunk, ChunkSize) < ChunkSize ) {
            __quex_assert(me->derived_input_character_tell(me) <= TargetIndex);
            return;
        }
    if( remaining_character_n ) 
        me->derived_input_character_read(me, (QUEX_TYPE_CHARACTER*)chunk, remaining_character_n);
   
    __quex_assert(me->derived_input_character_tell(me) <= TargetIndex);
}

QUEX_INLINE void
QUEX_NAME(Buffer_finish_seek_based_on_read_p)(QUEX_NAME(Buffer)* me)
{
    me->_lexeme_start_p                = me->_read_p;
    me->_character_at_lexeme_start     = me->_read_p[0];
#   ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    /* Seek was towards 'target - 1'
     * => Now, there must be at least one character before '_read_p'.
     *    Or if not, then the target was on the lower limit 0 and the '_read_p'
     *    stands on the buffer's content front.                              */
    me->_character_before_lexeme_start = me->_read_p > &me->_memory._front[1] ?
                                           me->_read_p[-1]
                                         : QUEX_SETTING_CHARACTER_NEWLINE_IN_ENGINE_CODEC;
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
}

QUEX_NAMESPACE_MAIN_CLOSE
#endif                  /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I */
