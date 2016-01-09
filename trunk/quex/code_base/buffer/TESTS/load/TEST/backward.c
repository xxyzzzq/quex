/* PURPOSE: Testin Buffer_load_backward()
 *
 * Before the load backward can be tested, the buffer is brought into a
 * state where 'end of stream' is detected. This ensures that the backward
 * load steps through the whole stream backwards.
 *
 * The load backward is tested sequentially. The '_read_p' is decremented
 * by a given 'delta' after each load. The '_lexeme_start_p' follows
 * the '_read_p' at a given distance. This is repeated until the begin of 
 * stream is reached. An iterator 'G_t' iterates over possible settings of
 * the '_read_p delta' and the '_lexeme_start_p delta'.
 *
 * The behavior is checked with a set of 'hwut_verify' conditions on the 
 * buffer's state and its relation to its setting before.
 *
 *
 * OUTPUTS:
 *    * adapted pointers: ._read_p, ._lexeme_start_p.
 *    * buffer's content.
 *    * input.end_p, 
 *      input.character_index_begin, 
 *      input.character_index_end_of_stream
 *
 * The read and lexeme pointers shall point exactly to the same character as
 * before the load procedure. That is, they need.                            */

/* 
<<hwut-iterator: G>> 
------------------------------------------------------------------------
#include <stdint.h>
------------------------------------------------------------------------
    ptrdiff_t read_p_delta;      ptrdiff_t lexeme_start_p_delta;               
    [ 1, 2, 3 ];                 |0:6|; 
------------------------------------------------------------------------
*/

#include "commonly_pasted.c"
#include <backward-gen.h>

static ptrdiff_t            test_load_backward(QUEX_NAME(Buffer)* buffer);
static ptrdiff_t            walk_backward(ptrdiff_t ReadPDelta, ptrdiff_t LexemeStartPDelta);
static void                 load_forward_until_eos(QUEX_NAME(Buffer)* me);

int
main(int argc, char**argv)
{
    G_t    it;
    int    count = 0;

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Buffer_load_backward: (BPC=%i, FB=%i);\n", 
               sizeof(QUEX_TYPE_CHARACTER),
               (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }

    G_init(&it);
    while( G_next(&it) ) {
        count += walk_backward(it.read_p_delta, it.lexeme_start_p_delta);
    }
    printf("<terminated %i>\n", (int)count);
    return 0;
}

static ptrdiff_t
walk_backward(ptrdiff_t ReadPDelta, ptrdiff_t LexemeStartPDelta)
/* Walk through file by incrementing the 'read_p' by 'ReadPDelta' until the 
 * end of file is reached. The 'lexeme_start_p' remains in a constant distance 
 * to 'read_p' given by 'LexemeStartPDelta'.                                 */
{
    QUEX_NAME(Buffer)             buffer;
    QUEX_NAME(ByteLoader_Memory)  loader;
    QUEX_NAME(LexatomLoader)*      filler;
    int                           count = 0;
    QUEX_TYPE_CHARACTER           memory[5];
    const int                     MemorySize = 5;

    QUEX_NAME(ByteLoader_Memory_construct)(&loader, 
                                           (uint8_t*)&PseudoFile[0], 
                                           (const uint8_t*)&PseudoFile[sizeof(PseudoFile)/sizeof(PseudoFile[0])]);
    filler = QUEX_NAME(LexatomLoader_new)(&loader.base, 
                                         (QUEX_NAME(Converter)*)0, 0);

    QUEX_NAME(Buffer_construct)(&buffer, filler,
                                &memory[0], MemorySize,
                                (QUEX_TYPE_CHARACTER*)0, E_Ownership_EXTERNAL); 

    load_forward_until_eos(&buffer);

    for(buffer._read_p =  &buffer.input.end_p[-1]; 
        buffer._read_p >= &buffer._memory._front[1];
        buffer._read_p -= ReadPDelta) {
        buffer._lexeme_start_p = buffer._read_p + LexemeStartPDelta;  
        if( buffer._lexeme_start_p >= &buffer._memory._back[-1] ) {
            buffer._lexeme_start_p =  &buffer._memory._back[-2];
        }
        if( buffer._lexeme_start_p <= buffer._memory._front ) {
            buffer._lexeme_start_p = &buffer._memory._front[1];
        }
        count += test_load_backward(&buffer);
    }
    return count;
}

static void
load_forward_until_eos(QUEX_NAME(Buffer)* me)
{
    int  count = 0;

    while( me->input.character_index_end_of_stream == -1 ) {
        me->_read_p         = me->input.end_p;
        me->_lexeme_start_p = me->input.end_p;
        QUEX_NAME(Buffer_load_forward)(me, NULL, 0);

        (void)verify_content(me);
        ++count;
        hwut_verify(count < 100);
    }
    hwut_verify(me->input.character_index_end_of_stream == sizeof(PseudoFile)/sizeof(PseudoFile[0])); 
}

static ptrdiff_t
test_load_backward(QUEX_NAME(Buffer)* buffer) 
{
    struct {
        QUEX_TYPE_CHARACTER*      read_p;
        QUEX_TYPE_CHARACTER*      lexeme_start_p;
        QUEX_TYPE_CHARACTER       read;
        QUEX_TYPE_CHARACTER       lexeme_start;
        QUEX_TYPE_CHARACTER*      position_register_1;
        QUEX_TYPE_CHARACTER*      position_register_3;
        QUEX_TYPE_STREAM_POSITION character_index_begin;
    } before;
    bool                 verdict_f;
    ptrdiff_t            delta;
    ptrdiff_t            count = 0;

#   if 0
    position_register[0]       = PoisonP; 
    before.position_register_1 = position_register[1] = random_between(buffer->_lexeme_start_p, buffer->_read_p);
    position_register[2]       = NullP;   
    before.position_register_3 = position_register[3] = random_between(buffer->_lexeme_start_p, buffer->_read_p);
    position_register[4]       = PoisonP; 
#   endif

    before.read_p                = buffer->_read_p;
    before.read                  = *buffer->_read_p;
    before.lexeme_start_p        = buffer->_lexeme_start_p;
    before.lexeme_start          = *buffer->_lexeme_start_p;
    before.character_index_begin = buffer->input.character_index_begin;

    verdict_f = QUEX_NAME(Buffer_load_backward)(buffer); 
    /* &position_register[1], PositionRegisterN); */

    delta = buffer->_read_p - before.read_p;
    if( delta ) { 
        hwut_verify(delta > 0);
        hwut_verify(delta <= buffer->_memory._back - &buffer->_memory._front[1]);
        /* NOT: hwut_verify(verdict_f);  
         * Because, even if no content has been loaded, the pointers may have
         * been adapted during the 'move-away' of passed content.            */
    }
    else {
        hwut_verify(! verdict_f);  
    }

    hwut_verify(before.character_index_begin >= buffer->input.character_index_begin);
    hwut_verify(before.character_index_begin -  buffer->input.character_index_begin == delta);

    hwut_verify(buffer->_lexeme_start_p - before.lexeme_start_p == delta);
#   if 0
    hwut_verify(position_register[0]       == PoisonP);
    hwut_verify(before.position_register_1 -  position_register[1] == delta);
    hwut_verify(position_register[2]       == NullP);
    hwut_verify(before.position_register_3 -  position_register[3] == delta);
    hwut_verify(position_register[4]       == PoisonP);
#   endif

    hwut_verify(*buffer->_read_p         == before.read);
    hwut_verify(*buffer->_lexeme_start_p == before.lexeme_start);

    /* Make sure that the content has been loaded properly. From the 
     * variable 'pseudo_file' it can be previewed what the content is 
     * supposed to be.                                                   */
    count += verify_content(buffer);
    hwut_verify(buffer->input.end_p[0] == QUEX_SETTING_BUFFER_LIMIT_CODE);

    return count + 1;
}

