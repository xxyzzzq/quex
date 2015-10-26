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

QUEX_INLINE void  QUEX_NAME(BufferMemory_construct)(QUEX_NAME(BufferMemory)*  me, 
                                                    QUEX_TYPE_CHARACTER*      Memory, 
                                                    const size_t              Size,
                                                    E_Ownership               Ownership);
QUEX_INLINE void  QUEX_NAME(BufferMemory_destruct)(QUEX_NAME(BufferMemory)* me);

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
    me->input.end_p                         = &me->_memory._front[1];
    me->input.character_index_begin         = 0;
    me->input.character_index_end_of_stream = -1;
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
    if( me->filler && me->filler->byte_loader ) {
        __quex_assert(! EndOfFileP);
        QUEX_NAME(Buffer_input_register)(me, BeginP, 0, false);     /* EMPTY */
        QUEX_NAME(Buffer_load_forward)(me);   
    } 
    else {
        __quex_assert(! EndOfFileP || (EndOfFileP >= BeginP && EndOfFileP <= EndP));
        (void)EndP;

        QUEX_NAME(Buffer_input_register)(me, EndOfFileP ? EndOfFileP : BeginP, 
                                         0, false);
    }

    QUEX_BUFFER_ASSERT_CONSISTENCY(me);
}

QUEX_INLINE void
QUEX_NAME(Buffer_input_register)(QUEX_NAME(Buffer)*        me,
                                 QUEX_TYPE_CHARACTER*      EndOfInputP,
                                 QUEX_TYPE_STREAM_POSITION CharacterIndexBegin,
                                 bool                      EndOfStreamFoundF)
/* Registers information about the stream that fills the buffer and its
 * relation to the buffer. 
 *  
 *  EndOfInputP --> Position behind the last character in the buffer that has
 *                  been streamed.
 *          '0' --> No change.
 *  
 *  CharacterIndexBegin --> Character index of the first character in the 
 *                          buffer.
 *                 '-1' --> No change.
 *  
 *  EndOfStreamFoundF --> True, of the end of stream has been reached.
 *                        False, else.
 *                                                                           */
{
    if( EndOfInputP ) {
        __quex_assert(EndOfInputP <= me->_memory._back);
        __quex_assert(EndOfInputP >  me->_memory._front);

        me->input.end_p    = EndOfInputP;
        *(me->input.end_p) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }

    if( CharacterIndexBegin != -1 ) {
        me->input.character_index_begin = CharacterIndexBegin;
    }

    if( EndOfStreamFoundF ) {
        me->input.character_index_end_of_stream = \
                CharacterIndexBegin + (EndOfInputP - &me->_memory._front[1]);
    }

    QUEX_IF_ASSERTS_poison(&me->input.end_p[1], me->_memory._back);
    /* NOT: assert(QUEX_NAME(Buffer_input_character_index_begin)(me) >= 0);
     * This function may be called before content is setup/loaded propperly. */ 
}

QUEX_INLINE bool
QUEX_NAME(Buffer_is_empty)(QUEX_NAME(Buffer)* me)
/* Setting the input.end_p = front meanse: buffer is empty.                  */
{ return me->input.end_p == me->_memory._front; }

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_input_character_index_end)(QUEX_NAME(Buffer)* me)
{
    __quex_assert(me->input.character_index_begin >= 0);
    QUEX_BUFFER_ASSERT_pointers_in_range(me);

    return me->input.character_index_begin + (me->input.end_p - &me->_memory._front[1]);
}

QUEX_INLINE QUEX_TYPE_STREAM_POSITION  
QUEX_NAME(Buffer_input_character_index_begin)(QUEX_NAME(Buffer)* me)
/* Determine character index of first character in the buffer.               */
{
    __quex_assert(me->input.character_index_begin >= 0);
    return me->input.character_index_begin;
}

QUEX_INLINE void
QUEX_NAME(Buffer_read_p_add_offset)(QUEX_NAME(Buffer)* buffer, const size_t Offset)
{ 
    QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
    buffer->_read_p += Offset; 
    QUEX_BUFFER_ASSERT_pointers_in_range(buffer);
}

QUEX_INLINE QUEX_TYPE_CHARACTER
QUEX_NAME(Buffer_input_get_offset)(QUEX_NAME(Buffer)* me, const ptrdiff_t Offset)
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
QUEX_NAME(Buffer_is_end_of_file)(QUEX_NAME(Buffer)* buffer)
{ 
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    return buffer->_read_p == buffer->input.end_p;
}

QUEX_INLINE bool                  
QUEX_NAME(Buffer_is_begin_of_file)(QUEX_NAME(Buffer)* buffer)
{ 
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    if     ( buffer->_read_p != buffer->_memory._front )                  return false;
    else if( QUEX_NAME(Buffer_input_character_index_begin)(buffer) != 0 ) return false;
    return true;
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
    move_distance = move_begin_p - BeginP;

    if( ! move_distance ) return (QUEX_TYPE_CHARACTER*)0;

    else if( move_size ) {
        /* Move.                                                             */
        __QUEX_STD_memmove((void*)BeginP, (void*)move_begin_p,
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
    }

    /* Pointer Adaption: _read_p, _lexeme_start_p, 
     *                   input.end_p, input.end_character_index              */
    me->_read_p -= move_distance;
    if( me->_lexeme_start_p ) {
        me->_lexeme_start_p -= move_distance;
    }

    /* input.end_p/end_character_index: End character index remains the SAME, 
     * since no new content has been loaded into the buffer.                 */
    __quex_assert(me->input.end_p - BeginP >= move_distance);

    QUEX_NAME(Buffer_input_register)(me, 
                                     &me->input.end_p[- move_distance], 
                                     me->input.character_index_begin + move_distance,
                                     false);

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

    /* input.end_p/end_character_index: End character index may CHANGE, since 
     * some of the loaded content is thrown away.                            */
    end_p = EndP - me->input.end_p < move_distance ? EndP
                                                   : &me->input.end_p[move_distance];

    QUEX_NAME(Buffer_input_register)(me, end_p, 
                                     me->input.character_index_begin - move_distance,
                                     false);

    /*_______________________________________________________________________*/
    QUEX_IF_ASSERTS_poison(BeginP, &BeginP[move_distance]); 
    QUEX_BUFFER_ASSERT_CONSISTENCY(me);

    return move_distance;
}

QUEX_INLINE size_t          
QUEX_NAME(BufferMemory_size)(QUEX_NAME(BufferMemory)* me)
{ return (size_t)(me->_back - me->_front + 1); }

QUEX_INLINE void
QUEX_NAME(Buffer_reverse_byte_order)(QUEX_TYPE_CHARACTER*       Begin, 
                                     const QUEX_TYPE_CHARACTER* End)
{
    uint8_t              tmp = 0xFF;
    QUEX_TYPE_CHARACTER* iterator = 0x0;

    switch( sizeof(QUEX_TYPE_CHARACTER) ) {
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

QUEX_INLINE void 
QUEX_NAME(BufferMemory_construct)(QUEX_NAME(BufferMemory)*  me, 
                                  QUEX_TYPE_CHARACTER*      Memory, 
                                  const size_t              Size,
                                  E_Ownership               Ownership) 
{
    __quex_assert(Memory);
    /* "Memory size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2" is reqired.
     * Maybe, define '-DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0' for 
     * compilation (assumed no pre-contexts.)                                */
    __quex_assert(Size > QUEX_SETTING_BUFFER_MIN_FALLBACK_N + 2);

    me->_front    = Memory;
    me->_back     = &Memory[Size-1];
    me->ownership = Ownership;
    *(me->_front) = QUEX_SETTING_BUFFER_LIMIT_CODE;
    *(me->_back)  = QUEX_SETTING_BUFFER_LIMIT_CODE;
}

QUEX_INLINE void 
QUEX_NAME(BufferMemory_destruct)(QUEX_NAME(BufferMemory)* me) 
/* Does not set 'me->_front' to zero, if it is not deleted. Thus, the user
 * may detect wether it needs to be deleted or not.                          */
{
    if( me->_front && me->ownership == E_Ownership_LEXICAL_ANALYZER ) {
        QUEXED(MemoryManager_free)((void*)me->_front, 
                                   E_MemoryObjectType_BUFFER_MEMORY);
        /* Protect against double-destruction.                               */
        me->_front = me->_back = (QUEX_TYPE_CHARACTER*)0x0;
    }
}

QUEX_INLINE bool
QUEX_NAME(Buffer_move_and_fill_forward)(QUEX_NAME(Buffer)*        me, 
                                        QUEX_TYPE_STREAM_POSITION NewCharacterIndexBegin)
/*
 * Before:    .-------------------------------------- prev character_index_begin             
 *            :                 
 *            | . . . . . . . . .x.x.x.x.x.x.x.x.x.x.x| 
 *                              |<---- move size ---->|
 * After:     |<- move distance |
 *            .-------------------------------------- new character_index_begin
 *            :                     .---------------- prev character index begin
 *            :                     :  
 *            |x.x.x.x.x.x.x.x.x.x.x|N.N.N.N.N.N.N.N.N| 
 *                                                             
 * Moves the region of size 'Size' from the end of the buffer to the beginning
 * of the buffer and tries to load as many characters as possible behind it.
 */
{
    QUEX_TYPE_CHARACTER*       BeginP      = &me->_memory._front[1];
    const ptrdiff_t            ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    QUEX_TYPE_STREAM_POSITION  load_character_index;
    ptrdiff_t                  load_request_n;
    QUEX_TYPE_CHARACTER*       load_p;
    ptrdiff_t                  loaded_n;
    intmax_t                   move_distance;
    ptrdiff_t                  move_size;

    __quex_assert(me->input.character_index_begin  <= NewCharacterIndexBegin);

    /* Move existing content in the buffer to appropriate position.          */
    move_distance = NewCharacterIndexBegin - me->input.character_index_begin;
    if( move_distance < ContentSize ) {
        move_size            = me->input.end_p - &BeginP[move_distance];
        load_character_index = NewCharacterIndexBegin + move_size;
        load_request_n       = ContentSize - move_size;  /* Try to load max. */
        load_p               = &BeginP[move_size];
        __QUEX_STD_memmove((void*)BeginP, (void*)&BeginP[move_distance], 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
    }
    else {
        move_size            = 0;
        load_character_index = NewCharacterIndexBegin;
        load_request_n       = ContentSize;              /* Try to load max. */
        load_p               = BeginP;
    }

    __quex_assert(load_character_index == NewCharacterIndexBegin + (load_p - BeginP));
    loaded_n = QUEX_NAME(BufferFiller_region_load)(me, load_p, load_request_n,
                                                   load_character_index);
    if( ! loaded_n ) {
        if( move_size ) {
            /* Nothing has been loaded => Buffer must be setup as before.    */
            __QUEX_STD_memmove((void*)&BeginP[move_distance], (void*)BeginP, 
                               (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
            loaded_n = QUEX_NAME(BufferFiller_region_load)(me, BeginP, move_size,
                                                           me->input.character_index_begin);
            if( loaded_n != move_size ) {
                QUEX_ERROR_EXIT("Buffer filler failed to load content that has been loaded before.!");
                return false;
            }
        }
        return false;
    }

    /* 'load_request_n != loaded_n' => End of stream detected.               */
    QUEX_NAME(Buffer_input_register)(me, &load_p[loaded_n], 
                                     NewCharacterIndexBegin, 
                                     load_request_n != loaded_n);
    return true;
}

QUEX_INLINE bool
QUEX_NAME(Buffer_move_and_fill_backward)(QUEX_NAME(Buffer)*        me, 
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
    QUEX_TYPE_CHARACTER*       BeginP      = &me->_memory._front[1];
    QUEX_TYPE_CHARACTER*       EndP        = me->_memory._back;
    const ptrdiff_t            ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(me);
    QUEX_TYPE_STREAM_POSITION  character_index_begin = QUEX_NAME(Buffer_input_character_index_begin)(me);
    ptrdiff_t                  load_request_n;
    ptrdiff_t                  loaded_n;
    intmax_t                   move_distance;
    ptrdiff_t                  move_size;
    QUEX_TYPE_CHARACTER*       end_p;

    __quex_assert(NewCharacterIndexBegin >= 0);
    __quex_assert(character_index_begin  >= NewCharacterIndexBegin);

    move_distance = character_index_begin - NewCharacterIndexBegin;
    if( move_distance < ContentSize ) {
        move_size = QUEX_MAX(0, QUEX_MIN(me->input.end_p - BeginP, 
                                         (ptrdiff_t)(ContentSize - move_distance)));
        __QUEX_STD_memmove((void*)&BeginP[move_distance], BeginP, 
                           (size_t)move_size * sizeof(QUEX_TYPE_CHARACTER));
        load_request_n = (ptrdiff_t)move_distance;
    }
    else {
        load_request_n = ContentSize;
    }

    loaded_n = QUEX_NAME(BufferFiller_region_load)(me, BeginP, load_request_n,
                                                   NewCharacterIndexBegin);
    if( loaded_n != load_request_n ) {
        QUEX_ERROR_EXIT("Buffer filler failed to load content that has been loaded before.!");
        return false;
    }

    /* Adapt 'end_p' and 'end_character_index'.                          */
    end_p = EndP - me->input.end_p < move_distance ? EndP
                                                   : &me->input.end_p[move_distance];
    QUEX_NAME(Buffer_input_register)(me, end_p, NewCharacterIndexBegin, false);
    return true;
}
   
QUEX_INLINE bool
QUEX_NAME(Buffer_load_forward)(QUEX_NAME(Buffer)* buffer)
/* Load as much new content into the buffer as possible--from what lies
 * ahead in the input stream. The '_read_p' and the '_lexeme_start_p' 
 * MUST be maintained inside the buffer. The 'input.end_p' pointer
 * and 'input.end_character_index' are adapted according to the newly
 * loaded content.
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_TYPE_CHARACTER*        BeginP      = &buffer->_memory._front[1];
    const ptrdiff_t             ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
    QUEX_TYPE_STREAM_POSITION   new_character_index_begin;
    QUEX_TYPE_STREAM_POSITION   character_index_begin = QUEX_NAME(Buffer_input_character_index_begin)(buffer);
    QUEX_TYPE_STREAM_POSITION   character_index_of_read_p;
    QUEX_TYPE_STREAM_POSITION   character_index_of_lexeme_p;
    QUEX_NAME(BufferFiller)*    me;

    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

    __quex_debug_buffer_load(buffer, "FORWARD(entry)\n");

    me = buffer->filler;
    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = Beginning of the Buffer: Reload nonsense. Maximum 
     *    size of available content lies ahead of '_read_p'.
     * -- input.end_p != 0: Tail of file read is already in buffer.          */
    if( ! me ) {
        return 0;                        /* Possible, if no filler specified */    
    }
    else if( buffer->_read_p - buffer->_lexeme_start_p >= ContentSize ) { 
        /* OVERFLOW: If stretch from _read_p to _lexeme_start_p 
         * spans the whole buffer, then nothing can be loaded.               */
        QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ true);
        return false;
    }

    character_index_of_read_p    = character_index_begin + (buffer->_read_p - BeginP);
    character_index_of_lexeme_p  = character_index_begin + (buffer->_lexeme_start_p - BeginP);
    new_character_index_begin = QUEX_MIN(character_index_of_read_p, character_index_of_lexeme_p);
    new_character_index_begin = QUEX_MAX(0, new_character_index_begin - QUEX_SETTING_BUFFER_MIN_FALLBACK_N);

    if( ! QUEX_NAME(Buffer_move_and_fill_forward)(buffer, new_character_index_begin) ) {
        /* No change to _read_p, _lexeme_start_p.                            */
        return false;
    }

    buffer->_read_p         = &BeginP[character_index_of_read_p   - new_character_index_begin];
    buffer->_lexeme_start_p = &BeginP[character_index_of_lexeme_p - new_character_index_begin];

    __quex_debug_buffer_load(buffer, "LOAD FORWARD(exit)\n");
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    return true;
}

QUEX_INLINE bool   
QUEX_NAME(Buffer_load_backward)(QUEX_NAME(Buffer)* buffer)
/* Load *previous* content into the buffer so that the analyzer can 
 * continue seeminglessly (in backward direction).
 *
 * RETURNS: Number of loaded buffer elements of type QUEX_TYPE_CHARACTER     */
{
    QUEX_NAME(BufferFiller)*   me       = buffer->filler;
    QUEX_TYPE_CHARACTER*       BeginP   = &buffer->_memory._front[1];
    QUEX_TYPE_CHARACTER*       EndP     = buffer->_memory._back;
    const ptrdiff_t            ContentSize = (ptrdiff_t)QUEX_NAME(Buffer_content_size)(buffer);
    QUEX_TYPE_STREAM_POSITION  character_index_begin = QUEX_NAME(Buffer_input_character_index_begin)(buffer);
    QUEX_TYPE_STREAM_POSITION  new_character_index_begin;
    QUEX_TYPE_STREAM_POSITION  character_index_of_read_p;
    QUEX_TYPE_STREAM_POSITION  character_index_of_lexeme_p;

#   ifdef QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION
    QUEX_ERROR_EXIT(__QUEX_MESSAGE_BUFFER_FILLER_ON_STRANGE_STREAM_IN_BACKWARD_LOAD);
#   endif
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);

    __quex_debug_buffer_load(buffer, "BACKWARD(entry)\n");

    /* REFUSE (return 0 indicating 'nothing loaded, but ok (>=0) !') if:
     * -- _read_p = End of the Buffer: Reload nonsense. Maximum size of
     *    available content lies before of '_read_p' for backward lexing..
     * -- input.end_character_index == 0: Stading at begin, already.         */
    if( ! me ) return false;         /* Possible, if no filler specified     */    
    else if( buffer->_lexeme_start_p >= &EndP[-1] ) { 
        /* If _lexeme_start_p at back, then no new content can be loaded.    */
        QUEX_NAME(__BufferFiller_on_overflow)(buffer, /* Forward */ false);
        return false;
    }

    character_index_of_read_p   = character_index_begin + (buffer->_read_p - BeginP);
    character_index_of_lexeme_p = character_index_begin + (buffer->_lexeme_start_p - BeginP);
    new_character_index_begin   = character_index_begin - (ContentSize >> 1);
    new_character_index_begin   = QUEX_MAX(character_index_of_read_p, 
                                           character_index_of_lexeme_p);
    new_character_index_begin   = new_character_index_begin > QUEX_SETTING_BUFFER_MIN_FALLBACK_N ?
                                    new_character_index_begin - QUEX_SETTING_BUFFER_MIN_FALLBACK_N
                                  : 0;

    if( ! QUEX_NAME(Buffer_move_and_fill_backward)(buffer, new_character_index_begin) )
        return false;

    buffer->_read_p         = &BeginP[character_index_of_read_p   - new_character_index_begin];
    buffer->_lexeme_start_p = &BeginP[character_index_of_lexeme_p - new_character_index_begin];

    __quex_debug_buffer_load(buffer, "BACKWARD(exit)\n");
    QUEX_BUFFER_ASSERT_CONSISTENCY(buffer);
    return true;
}

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer_navigation.i>

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__BUFFER_I */


