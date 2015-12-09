/* PURPOSE: Testin Buffer_load_forward()
 *
 * INPUTS:
 *    .input.end_p     = [Front, Inside, Back]
 *    ._read_p         = [Front, FallBack-1, FallBack, FallBack+1]
 *    ._lexeme_start_p = [Front, FallBack-1, FallBack, FallBack+1]
 *    BF.ci            = [0, != 0, LastCi, EndCi]
 *    .input.character_index_begin = [0, < BF.ci, == BF.ci, > BF.ci]
 *    .input.character_index_end_of_stream = [ -1, != -1]
 *
 *    where "BF.ci" is the BufferFiller's next_character_index_to_load, 
 *    "LastCi" the last character index, and "EndCi" the end character 
 *    index of the file.
 *
 *    Content to be loaded may: -- load until limit, 
 *                              -- load some content, or
 *                              -- not load anything at all.
 *
 * OUTPUTS:
 *    * adapted pointers: ._read_p, ._lexeme_start_p and position registers.
 *    * buffer's content.
 *    * input.end_p, 
 *      input.character_index_begin, 
 *      input.character_index_end_of_stream
 *
 * The read and lexeme pointers shall point exactly to the same character as
 * before the load procedure. That is, they need
 */

/* 
<<hwut-iterator: G>> 
------------------------------------------------------------------------
#include <stdint.h>
------------------------------------------------------------------------
    ptrdiff_t read_p_delta;            ptrdiff_t lexeme_start_p_delta;               
    [ 1, 2, 3 ];                 |0:6|; 
------------------------------------------------------------------------
*/

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/loader/ByteLoader_Memory>
#include <quex/code_base/buffer/loader/ByteLoader_Memory.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/single.i>
#include <hwut_unit.h>
#include <forward-gen.h>


static const QUEX_TYPE_CHARACTER  PseudoFile[] = {
   1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 13, 14, 15, 16, 
   17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
};
#define PSEUDO_FILE_SIZE  sizeof(PseudoFile)

static void                 test_load_forward(QUEX_NAME(Buffer)* buffer);
static QUEX_TYPE_CHARACTER* random_between(QUEX_TYPE_CHARACTER* A, QUEX_TYPE_CHARACTER* B);
static ptrdiff_t            walk_forward(ptrdiff_t ReadPDelta, ptrdiff_t LexemeStartPDelta);

int
main(int argc, char**argv)
{
    G_t    it;
    int    count = 0;

    G_init(&it);
    while( G_next(&it) ) {
        count += walk_forward(it.read_p_delta, it.lexeme_start_p_delta);
    }
    printf("<terminated %i>\n", (int)count);
    return 0;
}

static ptrdiff_t
walk_forward(ptrdiff_t ReadPDelta, ptrdiff_t LexemeStartPDelta)
/* Walk through file by incrementing the 'read_p' by 'ReadPDelta' until the 
 * end of file is reached. The 'lexeme_start_p' remains in a constant distance 
 * to 'read_p' given by 'LexemeStartPDelta'.                                 */
{
    QUEX_NAME(Buffer)             buffer;
    QUEX_NAME(ByteLoader_Memory)  loader;
    QUEX_NAME(BufferFiller)*      filler;
    int                           count = 0;
    QUEX_TYPE_CHARACTER           memory[5];
    const int                     MemorySize = 5;

    QUEX_NAME(ByteLoader_Memory_construct)(&loader, 
                                           &PseudoFile[0], &PseudoFile[PSEUDO_FILE_SIZE]);
    filler = QUEX_NAME(BufferFiller_new)(&loader.base, 
                                         (QUEX_NAME(Converter)*)0, 0);

    QUEX_NAME(Buffer_construct)(&buffer, filler,
                                &memory[0], MemorySize,
                                (QUEX_TYPE_CHARACTER*)0, E_Ownership_EXTERNAL); 

    for(buffer._read_p = &buffer._memory._front[1]; 
        buffer._read_p < buffer._memory._back; 
        buffer._read_p += ReadPDelta) {
        buffer._lexeme_start_p = buffer._read_p + LexemeStartPDelta;  
        if( buffer._lexeme_start_p >= buffer._memory._back ) {
            buffer._lexeme_start_p = &buffer._memory._back[-1];
        }
        if( buffer._lexeme_start_p <= buffer._memory._front ) {
            buffer._lexeme_start_p = &buffer._memory._front[1];
        }
        test_load_forward(&buffer);
        ++count;
    }
    return count;
}

static void
test_load_forward(QUEX_NAME(Buffer)* buffer) 
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
    QUEX_TYPE_CHARACTER* PoisonP = (QUEX_TYPE_CHARACTER*)0x5A5A5A5A; 
    QUEX_TYPE_CHARACTER* NullP   = (QUEX_TYPE_CHARACTER*)0; 
    size_t               PositionRegisterN = 3;
    QUEX_TYPE_CHARACTER* (position_register[5]);
    QUEX_TYPE_CHARACTER  expected;
    QUEX_TYPE_CHARACTER* p;

    position_register[0]       = PoisonP; 
    before.position_register_1 = position_register[1] = random_between(buffer->_lexeme_start_p, buffer->_read_p);
    position_register[2]       = NullP;   
    before.position_register_3 = position_register[3] = random_between(buffer->_lexeme_start_p, buffer->_read_p);
    position_register[4]       = PoisonP; 

    before.read_p         = buffer->_read_p;
    before.read           = *buffer->_read_p;
    before.lexeme_start_p = buffer->_lexeme_start_p;
    before.lexeme_start   = *buffer->_lexeme_start_p;

    before.character_index_begin = buffer->input.character_index_begin;

    /* User registers [1] until including [3], borders are poisoned. */
    verdict_f = QUEX_NAME(Buffer_load_forward)(buffer, &position_register[1], 
                                               PositionRegisterN);
    delta = before.read_p - buffer->_read_p;
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

    hwut_verify(buffer->input.character_index_begin >= before.character_index_begin);
    hwut_verify(buffer->input.character_index_begin - before.character_index_begin == delta);

    hwut_verify(before.lexeme_start_p      -  buffer->_lexeme_start_p   == delta);
    hwut_verify(position_register[0]       == PoisonP);
    hwut_verify(before.position_register_1 -  position_register[1] == delta);
    hwut_verify(position_register[2]       == NullP);
    hwut_verify(before.position_register_3 -  position_register[3] == delta);
    hwut_verify(position_register[4]       == PoisonP);

    hwut_verify(*buffer->_read_p         == before.read);
    hwut_verify(*buffer->_lexeme_start_p == before.lexeme_start);

    /* Make sure that the content has been loaded properly. From the 
     * variable 'pseudo_file' it can be previewed what the content is 
     * supposed to be.                                                   */
    for(p=&buffer->_memory._front[1]; p != buffer->input.end_p ; ++p) {
        expected = PseudoFile[buffer->input.character_index_begin + p - &buffer->_memory._front[1]];
        hwut_verify(*p == expected);
    }
    hwut_verify(buffer->input.end_p[0] == QUEX_SETTING_BUFFER_LIMIT_CODE);
}

static QUEX_TYPE_CHARACTER*
random_between(QUEX_TYPE_CHARACTER* A, QUEX_TYPE_CHARACTER* B)
{
    QUEX_TYPE_CHARACTER* min   = A > B ? B : A;
    QUEX_TYPE_CHARACTER* max   = A > B ? A : B;
    ptrdiff_t            delta = max - min;
    static uint32_t      seed  = 971;

    if( ! delta ) return min;

    seed = (seed << 16) % 537;
        
    return &min[seed % delta];
}

