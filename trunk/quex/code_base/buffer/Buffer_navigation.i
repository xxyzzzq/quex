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
    return QUEX_TYPE_CHARACTER_POSITION(buffer->_read_p, QUEX_NAME(Buffer_character_index_begin)(buffer));
#   else
    return (QUEX_TYPE_CHARACTER_POSITION)(buffer->_read_p);
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
    buffer->_read_p = Position.address;
#   else
    buffer->_read_p = Position;
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_character_index_begin)(QUEX_NAME(Buffer)* me)
{
    const ptrdiff_t           fill_level =   QUEX_NAME(Buffer_text_end)(me) 
                                           - &me->_memory._front[1];
    QUEX_TYPE_STREAM_POSITION result     =   me->input.end_character_index 
                                           - fill_level;
    __quex_assert(result >= 0);
    return result;
}

QUEX_INLINE bool  
QUEX_NAME(Buffer_move_forward)(QUEX_NAME(Buffer)* me, const ptrdiff_t CharacterN)
/* Move '_read_p' backwards by 'CharacterN'. This may involve reload in 
 * forward direction.                                                     */
{
    QUEX_TYPE_CHARACTER* content_end    = QUEX_NAME(Buffer_text_end)(me);
    ptrdiff_t            distance       = content_end - me->_read_p;
    ptrdiff_t            delta          = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta > distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.    */
        delta               -= distance;
        me->_read_p          = content_end;
        me->_lexeme_start_p  = me->_read_p;
        if( ! QUEX_NAME(BufferFiller_load_forward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.           */
            me->_read_p = QUEX_NAME(Buffer_text_end)(me);  
            return false;
        } 
        content_end = QUEX_NAME(Buffer_text_end)(me);
        distance    = content_end - me->_read_p;
    }

    me->_read_p                       += delta;
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
 * backward direction.                                                   */
{
    QUEX_TYPE_CHARACTER* content_begin  = QUEX_NAME(Buffer_content_front)(me);
    ptrdiff_t            distance       = me->_read_p - content_begin;
    ptrdiff_t            delta          = CharacterN;
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    while( delta > distance ) {
        /* _read_p + CharacterN < text_end, thus no reload necessary.    */
        delta               -= distance;
        me->_read_p          = content_begin;
        me->_lexeme_start_p  = me->_read_p - 1;
        if( ! QUEX_NAME(BufferFiller_load_backward)(me) ) {
            /* Alarm, buffer is now in some indetermined state.           */
            me->_read_p = content_begin;
            return false;
        } 
        content_begin = QUEX_NAME(Buffer_text_end)(me);
        distance      = me->_read_p - content_begin;
    }

    me->_read_p                      -= delta;
    me->_lexeme_start_p               = me->_read_p;
    me->_character_at_lexeme_start    = *(me->_lexeme_start_p);
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

    return DeltaToBufferBegin + QUEX_NAME(Buffer_character_index_begin)(me);
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
{ 
    /* STRATEGY: Starting from a certain point in the file we read characters
     *           Convert one-by-one until we reach the given character index. 
     *           This is, of course, incredibly inefficient but safe to work under
     *           all circumstances. Fillers should only rely on this function
     *           in case of no other alternative. Also, caching some information 
     *           about what character index is located at what position may help
     *           to increase speed.                                                */      
#   ifdef QUEX_OPTION_ASSERTS
    const QUEX_TYPE_STREAM_POSITION TargetIndex = me->tell_character_index(me) + (QUEX_TYPE_STREAM_POSITION)ForwardN;
#   endif

    /* START: We are now at character index 'CharacterIndex - remaining_character_n'.
     * LOOP:  It remains to interpret 'remaining_character_n' number of characters. Since 
     *        the interpretation is best done using a buffer, we do this in chunks.      */ 
    size_t               remaining_character_n = (size_t)ForwardN;
    const size_t         ChunkSize             = QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE;
    QUEX_TYPE_CHARACTER  chunk[QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE];

    __quex_assert(QUEX_SETTING_BUFFER_FILLER_SEEK_TEMP_BUFFER_SIZE >= 1);

    /* We CANNOT assume that end the end it will hold: 
     *
     *       __quex_assert(me->tell_character_index(me) == TargetIndex);
     *
     * Because, we do not know wether the stream actually has so many characters.     */
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
#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_NAVIGATION_I */
