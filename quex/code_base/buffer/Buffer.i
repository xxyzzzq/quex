/* vim:set ft=c: -*- C++ -*- */
#ifndef __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I
#define __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I

#include <quex/code_base/asserts>
#include <quex/code_base/buffer/asserts>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/filler/BufferFiller>
#include <quex/code_base/MemoryManager>

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE ptrdiff_t QUEX_NAME(Buffer_move_forward)(QUEX_NAME(Buffer)*  me, 
                                                     intmax_t            move_distance);
QUEX_INLINE void      QUEX_NAME(Buffer_move_forward_undo)(QUEX_NAME(Buffer)* me,
                                                          intmax_t           move_distance,
                                                          ptrdiff_t          move_size);
QUEX_INLINE ptrdiff_t QUEX_NAME(Buffer_move_backward)(QUEX_NAME(Buffer)* me, 
                                                      intmax_t           move_distance);

QUEX_INLINE void*     QUEX_NAME(Buffer_fill)(QUEX_NAME(Buffer)*  me, 
                                             const void*         ContentBegin,
                                             const void*         ContentEnd);
QUEX_INLINE void      QUEX_NAME(Buffer_fill_prepare)(QUEX_NAME(Buffer)*  me, 
                                                     void**              begin_p, 
                                                     const void**        end_p);
QUEX_INLINE void      QUEX_NAME(Buffer_fill_finish)(QUEX_NAME(Buffer)* me,
                                                    const void*        FilledEndP);
QUEX_INLINE void
QUEX_NAME(Buffer_construct)(QUEX_NAME(Buffer)*        me, 
                            QUEX_NAME(BufferFiller)*  filler,
                            QUEX_TYPE_CHARACTER*      memory,
                            const size_t              MemorySize,
                            QUEX_TYPE_CHARACTER*      EndOfFileP,
                            E_Ownership               Ownership)
{
    /* Ownership of InputMemory is passed to 'me->_memory'.                  */
    QUEX_NAME(BufferMemory_construct)(&me->_memory, memory, MemorySize, 
                                      Ownership); 
    
    me->on_buffer_content_change = (void (*)(const QUEX_TYPE_CHARACTER*, const QUEX_TYPE_CHARACTER*))0;

    /* Until now, nothing is loaded into the buffer.                         */
                                                                             
    /* By setting begin and end to zero, we indicate to the loader that      
     * this is the very first load procedure.                                */
    me->filler = filler;
    me->fill         = QUEX_NAME(Buffer_fill);
    me->fill_prepare = QUEX_NAME(Buffer_fill_prepare);
    me->fill_finish  = QUEX_NAME(Buffer_fill_finish);
    QUEX_NAME(Buffer_init_analyzis)(me, EndOfFileP);
}

QUEX_INLINE void
QUEX_NAME(Buffer_destruct)(QUEX_NAME(Buffer)* me)
{
    QUEX_NAME(BufferFiller_delete)(&me->filler); 
    QUEX_NAME(BufferMemory_destruct)(&me->_memory);
}

QUEX_INLINE void
QUEX_NAME(Buffer_init_analyzis)(QUEX_NAME(Buffer)*   me, 
                                QUEX_TYPE_CHARACTER* EndOfFileP) 
{
    QUEX_TYPE_CHARACTER*      BeginP = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER*      EndP   = me->_memory._back;

    /* (1) BEFORE LOAD: The pointers must be defined which restrict the 
     *                  fill region. 
     *
     * The first state in the state machine does not increment. Thus, the
     * input pointer is set to the first position, not before.               */
    me->_read_p         = BeginP;                            
    me->_lexeme_start_p = BeginP;                            
                                                                             
    /* No character covered yet -> '\0'.                                     */
    me->_character_at_lexeme_start = '\0';                                   
#   ifdef  __QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION                 
    /* When the buffer is initialized, a line begins. Signalize that.        */
    me->_character_before_lexeme_start = QUEX_SETTING_CHARACTER_NEWLINE_IN_ENGINE_CODEC;
#   endif

    /* (2) Load content, determine character indices of borders, determine
     *     end of file pointer.                                              */
    QUEX_NAME(Buffer_register_eos)(me, (QUEX_TYPE_STREAM_POSITION)-1);

    if( me->filler && me->filler->byte_loader ) {
        __quex_assert(! EndOfFileP);
        QUEX_NAME(Buffer_register_content)(me, BeginP, 0);          /* EMPTY */
        QUEX_NAME(Buffer_load_forward)(me);   
    } 
    else {
        __quex_assert(! EndOfFileP || (EndOfFileP >= BeginP && EndOfFileP <= EndP));
        (void)EndP;

        if( EndOfFileP ) {
            QUEX_NAME(Buffer_register_content)(me, EndOfFileP, 0);
            QUEX_NAME(Buffer_register_eos)(me, EndOfFileP - BeginP);
        }
        else {
            QUEX_NAME(Buffer_register_content)(me, BeginP, 0);
        }
    }

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
}

QUEX_INLINE void
QUEX_NAME(Buffer_register_content)(QUEX_NAME(Buffer)*        me,
                                   QUEX_TYPE_CHARACTER*      EndOfInputP,
                                   QUEX_TYPE_STREAM_POSITION CharacterIndexBegin)
/* Registers information about the stream that fills the buffer and its
 * relation to the buffer. 
 *  
 *  EndOfInputP --> Position behind the last character in the buffer that has
 *                  been streamed.
 *          '0' --> No change.
 *  
 *  CharacterIndexBegin --> Character index of the first character in the 
 *                          buffer.
 *                 '-1' --> No change.                                       */
{
    if( EndOfInputP ) {
        __quex_assert(EndOfInputP <= me->_memory._back);
        __quex_assert(EndOfInputP >  me->_memory._front);

        me->input.end_p    = EndOfInputP;
        *(me->input.end_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    if( CharacterIndexBegin != (QUEX_TYPE_STREAM_POSITION)-1 ) {
        me->input.character_index_begin = CharacterIndexBegin;
    }

    QUEX_IF_ASSERTS_poison(&me->input.end_p[1], me->_memory._back);
    /* NOT: assert(QUEX_NAME(Buffer_input_character_index_begin)(me) >= 0);
     * This function may be called before content is setup/loaded propperly. */ 
}

QUEX_INLINE void       
QUEX_NAME(Buffer_register_eos)(QUEX_NAME(Buffer)*        me,
                               QUEX_TYPE_STREAM_POSITION CharacterIndexEndOfStream)
{
    me->input.character_index_end_of_stream = CharacterIndexEndOfStream;
}

QUEX_INLINE bool
QUEX_NAME(Buffer_is_empty)(QUEX_NAME(Buffer)* me)
/* RETURNS: true, if buffer does not contain anything.
 *          false, else.                                                     */
{ 
    return    me->input.end_p == &me->_memory._front[1] 
           && me->input.character_index_begin == 0; 
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_input_character_index_end)(QUEX_NAME(Buffer)* me)
/* RETURNS: Character index of the character to which '.input.end_p' points.
 *                                                                           */
{
    __quex_assert(me->input.character_index_begin >= 0);
    QUEX_BUFFER_ASSERT_pointers_in_range(me);

    return   me->input.character_index_begin 
           + (me->input.end_p - &me->_memory._front[1]);
}

QUEX_INLINE void
QUEX_NAME(Buffer_read_p_add_offset)(QUEX_NAME(Buffer)* buffer, const size_t Offset)
/* Add offset to '._read_p'. No check applies whether this is admissible.
 *                                                                           */
{ 
    QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
    buffer->_read_p += Offset; 
    QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
}

QUEX_INLINE QUEX_TYPE_CHARACTER
QUEX_NAME(Buffer_input_get_offset)(QUEX_NAME(Buffer)* me, 
                                   const ptrdiff_t Offset)
{
    QUEX_BUFFER_ASSERT_pointers_in_range(me);
    __quex_assert( me->_read_p + Offset > me->_memory._front );
    __quex_assert( me->_read_p + Offset <= me->_memory._back );
    return *(me->_read_p + Offset); 
}

QUEX_INLINE QUEX_TYPE_CHARACTER*
QUEX_NAME(Buffer_content_front)(QUEX_NAME(Buffer)* me)
{
    return me->_memory._front + 1;
}

QUEX_INLINE QUEX_TYPE_CHARACTER*
QUEX_NAME(Buffer_content_back)(QUEX_NAME(Buffer)* me)
{
    return me->_memory._back - 1;
}

QUEX_INLINE size_t
QUEX_NAME(Buffer_content_size)(QUEX_NAME(Buffer)* me)
{
    return QUEX_NAME(BufferMemory_size)(&(me->_memory)) - 2;
}

QUEX_INLINE bool 
QUEX_NAME(Buffer_is_end_of_file)(QUEX_NAME(Buffer)* me)
{ 
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    if     ( me->_read_p != me->input.end_p )                return false;
    else if( me->input.character_index_end_of_stream == -1 ) return false;

    return    QUEX_NAME(Buffer_input_character_index_end)(me) 
           == me->input.character_index_end_of_stream;
}

QUEX_INLINE bool                  
QUEX_NAME(Buffer_is_begin_of_file)(QUEX_NAME(Buffer)* buffer)
{ 
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    if     ( buffer->_read_p != buffer->_memory._front )                  return false;
    else if( QUEX_NAME(Buffer_input_character_index_begin)(buffer) != 0 ) return false;
    else                                                                  return true;
}

QUEX_INLINE QUEX_TYPE_CHARACTER*
QUEX_NAME(Buffer_move_away_passed_content)(QUEX_NAME(Buffer)* me)
/* Free some space AHEAD so that new content can be loaded. Content that 
 * is still used, or expected to be used shall remain inside the buffer.
 * Following things need to be respected:
 *
 *    _lexeme_start_p  --> points to the lexeme that is currently treated.
 *                         MUST BE INSIDE BUFFER!
 *    _read_p          --> points to the character that is currently used
 *                         for triggering. MUST BE INSIDE BUFFER!
 *    fall back region --> A used defined buffer backwards from the lexeme
 *                         start. Shall help to avoid extensive backward
 *                         loading.
 *
 * RETURNS: Pointer to the end of the maintained content.                    */
{ 
    QUEX_TYPE_CHARACTER*        BeginP = &me->_memory._front[1];
    const QUEX_TYPE_CHARACTER*  EndP   = me->_memory._back;
    QUEX_TYPE_CHARACTER*        move_begin_p;
    ptrdiff_t                   move_size;
    ptrdiff_t                   move_distance;
    const ptrdiff_t             FallBackN   = (ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    /* Determine from where the region-to-be-moved BEGINS, what its size is
     * and how far it is to be moved.                                        */
    move_begin_p  = me->_read_p;
    move_begin_p  = me->_lexeme_start_p ? QUEX_MIN(move_begin_p, me->_lexeme_start_p)
                                        : move_begin_p;
    /* Plain math: move_begin_p = max(BeginP, move_begin_p - FallBackN); 
     * BUT: Consider case where 'move_begin_p - FallBackN < 0'! CAREFUL!     */
    move_begin_p  = move_begin_p - BeginP < FallBackN ? BeginP 
                                                      : &move_begin_p[- FallBackN];
    move_size     = me->input.end_p - move_begin_p;
    move_distance = move_begin_p    - BeginP;

    if( ! move_distance ) return (QUEX_TYPE_CHARACTER*)0;

    else if( move_size ) {
        __QUEX_STD_memmove((void*)BeginP, (void*)move_begin_p,
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
    }

    /* Pointer Adaption: _read_p, _lexeme_start_p, 
     *                   input.end_p, input.end_character_index              */
    me->_read_p -= move_distance;
    if( me->_lexeme_start_p ) me->_lexeme_start_p -= move_distance;

    /* input.end_p/end_character_index: End character index remains the SAME, 
     * since no new content has been loaded into the buffer.                 */
    __quex_assert(me->input.end_p - BeginP >= move_distance);

    QUEX_NAME(Buffer_register_content)(me, &me->input.end_p[- move_distance], 
                                       me->input.character_index_begin + move_distance);

    /*_______________________________________________________________________*/
    QUEX_IF_ASSERTS_poison(&EndP[- move_distance], EndP);
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    (void)EndP;

    return &move_begin_p[move_size - move_distance];
}

QUEX_INLINE ptrdiff_t        
QUEX_NAME(Buffer_move_away_upfront_content)(QUEX_NAME(Buffer)* me)
/* Free some space in the REAR so that previous content can be re-loaded. Some 
 * content is to be left in front, so that no immediate reload is necessary
 * once the analysis goes forward again. Following things need to be respected:
 *
 *    _lexeme_start_p  --> points to the lexeme that is currently treated.
 *                         MUST BE INSIDE BUFFER!
 *    _read_p          --> points to the character that is currently used
 *                         for triggering. MUST BE INSIDE BUFFER!
 *
 * RETURNS: Distance the the buffer content has been freed to be filled.     */
{
    const QUEX_TYPE_CHARACTER*       BeginP      = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER*             EndP        = me->_memory._back;
    const ptrdiff_t                  ContentSize = EndP - BeginP;
    const QUEX_TYPE_CHARACTER*       move_end_p;
    ptrdiff_t                        move_distance;
    ptrdiff_t                        move_size;
    QUEX_TYPE_CHARACTER*             end_p;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    /* The begin character index should never be negative--one cannot read
     * before the first byte of a stream. 
     * --> move_distance      <= begin_character_index                       */

    /* Determine where the region-to-be-moved ENDS, what its size is and how
     * far it is to be moved.                                                */
    move_distance = EndP - me->input.end_p;
    move_distance = QUEX_MAX(move_distance, (ptrdiff_t)(ContentSize/3));
    move_distance = (ptrdiff_t)QUEX_MIN((QUEX_TYPE_STREAM_POSITION)move_distance, 
                                        me->input.character_index_begin);
    move_distance = QUEX_MIN(move_distance, &EndP[-1] - me->_read_p);
    if( me->_lexeme_start_p ) {
        move_distance = QUEX_MIN(move_distance, &EndP[-1] - me->_lexeme_start_p);
    }
    move_end_p    = EndP - move_distance;
    move_size     = move_end_p - BeginP;

    if( ! move_distance ) return 0;

    if( move_size ) {
        /* Move.                                                             */
        __QUEX_STD_memmove((void*)&BeginP[move_distance], (void*)BeginP, 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
    }

    /* Pointer Adaption: _read_p, _lexeme_start_p.                           */
    me->_read_p += move_distance;
    if( me->_lexeme_start_p ) {
        me->_lexeme_start_p += move_distance;
    }

    /* Adapt and of content pointer and new character index at begin.        */
    end_p = EndP - me->input.end_p < move_distance ? EndP
                                                   : &me->input.end_p[move_distance];

    QUEX_NAME(Buffer_register_content)(me, end_p, 
                                       me->input.character_index_begin - move_distance);

    /*_______________________________________________________________________*/
    QUEX_IF_ASSERTS_poison(BeginP, &BeginP[move_distance]); 
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    return move_distance;
}

QUEX_INLINE bool
QUEX_NAME(Buffer_move_and_load_forward)(QUEX_NAME(Buffer)*        me, 
                                        QUEX_TYPE_STREAM_POSITION NewCharacterIndexBegin,
                                        QUEX_TYPE_STREAM_POSITION MinCharacterIndexInBuffer)
/* RETURNS:  true -- if the the buffer could be filled start from 
 *                   NewCharacterIndexBegin.
 *           false, else.
 *
 * In case, that the loading fails, the buffer is setup as it was BEFORE the call
 * to this function.
 *
 * EXPLANATION:
 *
 * Before:    .-------------------------------------- prev character_index_begin             
 *            :                 
 *            | . . . . . . . . .x.x.x.x.x.x.x.x.x.x.x| 
*                               |<---- move size ---->|
 * After:     |<- move distance |
 *            .-------------------------------------- new character_index_begin
 *            :                     .---------------- prev character index begin
 *            :                     :  
 *            |x.x.x.x.x.x.x.x.x.x.x|N.N.N.N.N.N.N. . | 
 *            |- move_size -------->|- loaded_n ->|
 *                                                             
 * Moves the region of size 'Size' from the end of the buffer to the beginning
 * of the buffer and tries to load as many characters as possible behind it. */
{
    QUEX_TYPE_CHARACTER*       BeginP      = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER*       EndP        = me->_memory._back;
    const ptrdiff_t            ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    QUEX_TYPE_STREAM_POSITION  load_character_index;
    ptrdiff_t                  load_request_n;
    QUEX_TYPE_CHARACTER*       load_p;
    ptrdiff_t                  loaded_n;
    intmax_t                   move_distance;
    ptrdiff_t                  move_size;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    __quex_assert(me->input.character_index_begin      <= NewCharacterIndexBegin);
    __quex_assert(NewCharacterIndexBegin               <= MinCharacterIndexInBuffer);
    __quex_assert(NewCharacterIndexBegin + ContentSize >= MinCharacterIndexInBuffer );

    if(    me->input.character_index_end_of_stream != -1
        && MinCharacterIndexInBuffer >= me->input.character_index_end_of_stream ) {
        /* If the end of the stream is INSIDE the buffer already, then there
         * is no need, no chance, of loading more content.                   */
        return false;
    }

    /* (1) Move existing content in the buffer to appropriate position.      */
    move_distance = NewCharacterIndexBegin - me->input.character_index_begin;
    move_size            = QUEX_NAME(Buffer_move_forward)(me, move_distance);
    load_character_index = NewCharacterIndexBegin + move_size;
    load_request_n       = ContentSize - move_size; 
    load_p               = &BeginP[move_size];

    __quex_assert(load_character_index == NewCharacterIndexBegin + (load_p - BeginP));
    __quex_assert(load_p >= BeginP);
    __quex_assert(&load_p[load_request_n] <= EndP);
    (void)EndP;
    loaded_n = QUEX_NAME(BufferFiller_load)(me->filler, load_p, load_request_n,
                                            load_character_index);

    if( loaded_n != load_request_n ) { /* End of stream detected.            */
        QUEX_NAME(Buffer_register_eos)(me, load_character_index + loaded_n);
    }

    /* (3) In case of failure, restore previous buffer content.              */
    if( MinCharacterIndexInBuffer >= load_character_index + loaded_n ) {
        QUEX_NAME(Buffer_move_forward_undo)(me, move_distance, move_size);
        return false;
    }

    QUEX_NAME(Buffer_register_content)(me, &load_p[loaded_n], NewCharacterIndexBegin);
    return true;
}

QUEX_INLINE bool
QUEX_NAME(Buffer_move_and_load_backward)(QUEX_NAME(Buffer)*        me, 
                                         QUEX_TYPE_STREAM_POSITION NewCharacterIndexBegin)
/* Before:                     
 *            .------------------------------------- prev character index begin
 *            :
 *            |x.x.x.x.x.x.x.x.x.x. . . . . . . . . . . . . |
 *            |<--- move size---->|                         
 * After:                                             
 *            .------------------------------------- new character index begin
 *            :                     .--------------- prev character index begin
 *            :                     :
 *            :--- move distance--->|                 
 *            |N.N.N.N.N.N.N.N.N.N.N.x.x.x.x.x.x.x.x.x.x. . | 
 *                               
 * Moves the region of size 'Size' from the beginning of the buffer to the end
 * and tries to load as many characters as possible behind it. If the try fails
 * something is seriously wrong.                                             */
{
    QUEX_TYPE_CHARACTER*       BeginP   = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER*       EndP     = me->_memory._back;
    QUEX_TYPE_STREAM_POSITION  ci_begin = QUEX_NAME(Buffer_input_character_index_begin)(me);
    ptrdiff_t                  load_request_n;
    ptrdiff_t                  loaded_n;
    intmax_t                   move_distance;
    QUEX_TYPE_CHARACTER*       end_p;

    __quex_assert(NewCharacterIndexBegin >= 0);
    __quex_assert(ci_begin  >= NewCharacterIndexBegin);

    /* (1) Move away content, so that previous content can be reloaded.      */
    move_distance  = ci_begin - NewCharacterIndexBegin;
    load_request_n = QUEX_NAME(Buffer_move_backward)(me, move_distance);

    __quex_assert(&BeginP[load_request_n] <= EndP);

    /* (2) Move away content, so that previous content can be reloaded.      */
    loaded_n = QUEX_NAME(BufferFiller_load)(me->filler, BeginP, load_request_n,
                                            NewCharacterIndexBegin);

    /* (3) In case of error, the stream must have been corrupted. Previously
     *     present content is not longer available. Continuation impossible. */
    if( loaded_n != load_request_n ) {
        QUEX_ERROR_EXIT("Buffer filler failed to load content that has been loaded before.!");
        return false;
    }

    end_p = EndP - me->input.end_p < move_distance ? 
            EndP : &me->input.end_p[move_distance];

    QUEX_NAME(Buffer_register_content)(me, end_p, NewCharacterIndexBegin);
    return true;
}
   
QUEX_INLINE bool
QUEX_NAME(Buffer_load_forward)(QUEX_NAME(Buffer)* me)
/* Load as much new content into the buffer as possible--from what lies
 * ahead in the input stream. The '_read_p' and the '_lexeme_start_p' 
 * MUST be maintained inside the buffer. The 'input.end_p' pointer
 * and 'input.end_character_index' are adapted according to the newly
 * loaded content.
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_TYPE_CHARACTER*        BeginP      = &me->_memory._front[1];
    const ptrdiff_t             ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    QUEX_TYPE_STREAM_POSITION   ci_begin    = QUEX_NAME(Buffer_input_character_index_begin)(me);
    QUEX_TYPE_STREAM_POSITION   new_ci_begin;
    ptrdiff_t                   delta;

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = Beginning of the Buffer: Reload nonsense. Maximum 
     *    size of available content lies ahead of '_read_p'.
     * -- input.end_p != 0: Tail of file read is already in buffer.          */
    if( ! me->filler || ! me->filler->byte_loader ) {
        QUEX_NAME(Buffer_register_eos)(me, ci_begin + (me->input.end_p - BeginP));
        return false;                    /* Buffer based analysis.           */
    }
    else if( me->_read_p - me->_lexeme_start_p >= ContentSize ) { 
        /* OVERFLOW: If stretch from _read_p to _lexeme_start_p 
         * spans the whole buffer, then nothing can be loaded.               */
        QUEX_NAME(__BufferFiller_on_overflow)(me, /* Forward */ true);
        return false;
    }

    delta        = QUEX_MIN(me->_read_p, me->_lexeme_start_p) - BeginP;
    new_ci_begin = ci_begin + delta;
    /* QUEX_MIN(character_index_of_read_p, character_index_of_lexeme_p);     */
    /* If the fallback region cannot be established, then forget about it.   */
    if( delta > (ptrdiff_t)QUEX_SETTING_BUFFER_MIN_FALLBACK_N ) {
        new_ci_begin = QUEX_MAX(0, new_ci_begin - QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        delta        = (ptrdiff_t)(new_ci_begin - ci_begin);
    }

    if( ! QUEX_NAME(Buffer_move_and_load_forward)(me, new_ci_begin, new_ci_begin) ) {
        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        /* No change to _read_p, _lexeme_start_p.                            */
        return false;
    }
    me->_read_p         -= delta; 
    me->_lexeme_start_p -= delta; 

    __quex_debug_buffer_load(me, "LOAD FORWARD(exit)\n");
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return true;
}

QUEX_INLINE bool   
QUEX_NAME(Buffer_load_backward)(QUEX_NAME(Buffer)* me)
/* Load *previous* content into the buffer so that the analyzer can 
 * continue seeminglessly (in backward direction).
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_TYPE_CHARACTER*       EndP   = me->_memory._back;
    const ptrdiff_t            ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    QUEX_TYPE_STREAM_POSITION  ci_begin = QUEX_NAME(Buffer_input_character_index_begin)(me);
    QUEX_TYPE_STREAM_POSITION  new_ci_begin;
    ptrdiff_t                  delta;

#   ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
    QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM_IN_BACKWARD_LOAD);
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    __quex_debug_buffer_load(me, "BACKWARD(entry)\n");

    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = End of the Buffer: Reload nonsense. Maximum size of
     *    available content lies before of '_read_p' for backward lexing..
     * -- input.end_ci == 0: Stading at begin, already.         */
    if( ! me->filler || ! me->filler->byte_loader ) {
        return 0;                        /* Buffer based analysis.           */
    }
    else if( me->_lexeme_start_p >= &EndP[-1] ) { 
        /* If _lexeme_start_p at back, then no new content can be loaded.    */
        QUEX_NAME(__BufferFiller_on_overflow)(me, /* Forward */ false);
        return false;
    }

    delta          = ContentSize >> 1;
    delta          = QUEX_MIN(delta, 
                              &EndP[-1] - QUEX_MAX(me->_read_p, me->_lexeme_start_p));
    new_ci_begin   = QUEX_MIN(0, ci_begin - delta);

    delta          = (ptrdiff_t)(ci_begin - new_ci_begin);
    if( ! QUEX_NAME(Buffer_move_and_load_backward)(me, new_ci_begin) ) {
        QUEX_BUFFER_ASSERT_CONSISTENCY(me);
        return false;
    }

    me->_read_p         += delta; 
    me->_lexeme_start_p += delta; 

    __quex_debug_buffer_load(me, "BACKWARD(exit)\n");
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
    return true;
}

QUEX_INLINE ptrdiff_t
QUEX_NAME(Buffer_move_forward)(QUEX_NAME(Buffer)* me, 
                               intmax_t           move_distance)
/* RETURNS: Size of the moved region.                                        */
{
    QUEX_TYPE_CHARACTER* BeginP     = &me->_memory._front[1];
    const ptrdiff_t      FilledSize = me->input.end_p - BeginP;
    ptrdiff_t            move_size;

    if( move_distance >= FilledSize ) return 0;

    move_size = me->input.end_p - &BeginP[move_distance];
    if( move_distance ) {
        __QUEX_STD_memmove((void*)BeginP, (void*)&BeginP[move_distance], 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
    }
    return move_size;
}

QUEX_INLINE void
QUEX_NAME(Buffer_move_forward_undo)(QUEX_NAME(Buffer)* me,
                                    intmax_t           move_distance,
                                    ptrdiff_t          move_size)
{
    QUEX_TYPE_CHARACTER* BeginP      = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER* EndP        = me->_memory._back;
    const ptrdiff_t      ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    ptrdiff_t            load_request_n;
    ptrdiff_t            loaded_n;

    /* Character with character index 'MinCharacterIndexInBuffer' has
     * not been loaded. => Buffer must be setup as before.                   */
    if( move_size ) {
        __QUEX_STD_memmove((void*)&BeginP[move_distance], (void*)BeginP, 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
        load_request_n = (ptrdiff_t)move_distance;
    }
    else {
        load_request_n = (ptrdiff_t)ContentSize;
    }
    __quex_assert(&BeginP[load_request_n] <= EndP);
    (void)EndP;
    loaded_n = QUEX_NAME(BufferFiller_load)(me->filler, BeginP, load_request_n,
                                            me->input.character_index_begin);

    if( loaded_n != load_request_n ) {
        QUEX_ERROR_EXIT("Buffer filler failed to load content that has been loaded before.!");
    }
    else {
        /* Ensure, that the buffer limit code is restored.                   */
        *(me->input.end_p) = (QUEX_TYPE_CHARACTER)QUEX_SETTING_BUFFER_LIMIT_CODE;
    }
}

QUEX_INLINE ptrdiff_t
QUEX_NAME(Buffer_move_backward)(QUEX_NAME(Buffer)* me, intmax_t move_distance)
/* Moves content so that previous content may be filled into the buffer.
 *
 * RETURNS: Number of character that need to be filled into the gap.
 *                                                                           */
{
    QUEX_TYPE_CHARACTER*  BeginP      = &me->_memory._front[1];
    const ptrdiff_t       ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    ptrdiff_t             move_size;

    if( move_distance < ContentSize ) {
        move_size = QUEX_MIN(me->input.end_p - BeginP, 
                             ContentSize - (ptrdiff_t)move_distance);
        move_size = QUEX_MAX(0, move_size);

        __QUEX_STD_memmove((void*)&BeginP[move_distance], BeginP, 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
        return (ptrdiff_t)move_distance;
    }
    else {
        return ContentSize;
    }
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer_navigation.i>
#include <quex/code_base/buffer/Buffer_fill.i>
#include <quex/code_base/buffer/BufferMemory.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I */


