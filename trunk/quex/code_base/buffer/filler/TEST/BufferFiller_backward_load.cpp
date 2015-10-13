#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/filler/BufferFiller_Plain.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    using namespace quex;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Load Backward: Character=%i Byte(s), Fallback=%i\n", 
               sizeof(QUEX_TYPE_CHARACTER), (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    const size_t                    MemorySize = 12;
    const size_t                    BeginIdx   = 15;
    const size_t                    EndIdx     = BeginIdx + (MemorySize-2);

    QUEX_NAME(Buffer)               buffer;
    FILE*                           fh = prepare_input(); /* Festgemauert ... */
    ByteLoader*                     byte_loader; 
    QUEX_NAME(BufferFiller_Plain)*  filler;
    QUEX_TYPE_CHARACTER             memory[MemorySize];

    fseek(fh, BeginIdx * sizeof(QUEX_TYPE_CHARACTER), SEEK_SET); 

    /* When the filler is created, the current position of the byte loader is treated
     * as reference position. */
    byte_loader = ByteLoader_FILE_new(fh);
    filler      = (QUEX_NAME(BufferFiller_Plain)*)QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    QUEX_NAME(Buffer_construct)(&buffer, 
                                &filler->base, &memory[0], MemorySize, 0, 
                                E_Ownership_EXTERNAL);

    /* Simulate, as if we started at 0, and now reached '15'                 */
    byte_loader->initial_position    = 0;

    buffer._read_p                   = &buffer._memory._back[-1];
    buffer._lexeme_start_p           = &buffer._memory._back[-1];
    buffer.input.end_p               = (QUEX_TYPE_CHARACTER*)0;
    buffer.input.end_character_index = EndIdx;

    do {
        printf("------------------------------------------------------------\n");
        QUEX_NAME(Buffer_show_byte_content)(&buffer, 5);
        printf("     ");
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");
        if( QUEX_NAME(Buffer_input_begin_character_index)(&buffer) == 0 ) break;
        buffer._read_p         = buffer._memory._front;
        buffer._lexeme_start_p = &buffer._memory._front[1];
        /**/
        (void)QUEX_NAME(BufferFiller_load_backward)(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    filler->base.delete_self(&filler->base);
}


