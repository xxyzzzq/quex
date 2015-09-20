#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I
/* PURPOSE: Buffer-seek, i.e. setting the '_read_p' to a specific position
 *          in the stream.
 *
 * It is crucial to understand the difference between 'stream seeking' and 
 * 'buffer seeking'. Stream seeking determines the next position in the input
 * stream from where content is loaded into the buffer. Buffer seeking sets
 * the input pointer '_read_p' to a particular position. The position-1 where 
 * it points contains the next character to be read during analysis.           
 *
 * (C) Frank-Rene Schaefer                                                   */

QUEX_NAMESPACE_MAIN_OPEN

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
QUEX_NAME(Buffer_move_forward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_read_p' forwards by 'CharacterN'. This may involve reload in 
 * forward direction.                                                     
 * 
 * RETURNS: True -- if positioning was succesfull,
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER* content_end     = QUEX_NAME(Buffer_text_end)(me);
    ptrdiff_t            max_distance    = content_end - me->_read_p;
    ptrdiff_t            remaining_delta = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( remaining_delta > max_distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        remaining_delta     -= max_distance;
        me->_read_p          = content_end;
        me->_lexeme_start_p  = me->_read_p;
        if( ! QUEX_NAME(BufferFiller_load_forward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.              */
            me->_read_p         = QUEX_NAME(Buffer_text_end)(me);  
            me->_lexeme_start_p = me->_read_p;
            return false;
        } 
        content_end  = QUEX_NAME(Buffer_text_end)(me);
        max_distance = content_end - me->_read_p;
    }

    me->_read_p                       += remaining_delta;
    me->_lexeme_start_p                = me->_read_p;
    me->_character_at_lexeme_start     = *(me->_lexeme_start_p);
#   ifdef __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION
    me->_character_before_lexeme_start = *(me->_lexeme_start_p - 1);
#   endif

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return true;
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_move_backward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_read_p' backwards by 'CharacterN'. This may involve reload in 
 * backward direction.                                                   
 * 
 * RETURNS: True -- if positioning was succesfull,
 *          False -- else.                                                   */
{
    QUEX_TYPE_CHARACTER* content_begin   = QUEX_NAME(Buffer_content_front)(me);
    ptrdiff_t            max_distance    = me->_read_p - content_begin;
    ptrdiff_t            remaining_delta = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( remaining_delta > max_distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.        */
        remaining_delta     -= max_distance;                                    
        me->_read_p          = content_begin;                               
        me->_lexeme_start_p  = me->_read_p - 1;                             
        if( ! QUEX_NAME(BufferFiller_load_backward)(me) ) {                 
            /* Alarm, buffer is now in some indetermined state.              */
            me->_read_p = content_begin;
            return false;
        } 
        content_begin = QUEX_NAME(Buffer_text_end)(me);
        max_distance  = me->_read_p - content_begin;
    }

    me->_read_p                       -= remaining_delta;
    me->_lexeme_start_p                = me->_read_p;
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
        QUEX_NAME(Buffer_move_forward)(me, (ptrdiff_t)(CharacterIndex - CurrentCharacterIndex));
    }
    else {
        QUEX_NAME(Buffer_move_backward)(me,(ptrdiff_t)(CurrentCharacterIndex - CharacterIndex));
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
    const QUEX_TYPE_STREAM_POSITION TargetIndex =   me->tell_character_index(me) 
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
     *       __quex_assert(me->tell_character_index(me) == TargetIndex);
     *
     * Because, its unknown wether the stream has enough characters.         */
    for(; remaining_character_n > ChunkSize; remaining_character_n -= ChunkSize )  
        if( me->read_characters(me, (QUEX_TYPE_CHARACTER*)chunk, ChunkSize) < ChunkSize ) {
            __quex_assert(me->tell_character_index(me) <= TargetIndex);
            return;
        }
    if( remaining_character_n ) 
        me->read_characters(me, (QUEX_TYPE_CHARACTER*)chunk, remaining_character_n);
   
    __quex_assert(me->tell_character_index(me) <= TargetIndex);
}

QUEX_NAMESPACE_MAIN_CLOSE
#endif                  /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I */
