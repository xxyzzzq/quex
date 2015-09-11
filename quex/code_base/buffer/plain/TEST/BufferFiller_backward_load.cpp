#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

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
    QUEX_NAME(Buffer_construct)(&buffer, &filler->base, &memory[0], MemorySize, 0, 
                                E_Ownership_EXTERNAL);

    /* Simulate, as if we started at 0, and now reached '15' */
    byte_loader->initial_position         = 0;
    buffer._content_character_index_end   = BeginIdx + (MemorySize-2);
    //filler->_character_index            = buffer._content_character_index_begin + (MemorySize-2);
    filler->_last_stream_position         = ftell(fh);

    do {
        printf("------------------------------------------------------------\n");
        QUEX_NAME(Buffer_show_byte_content)(&buffer, 5);
        printf("     ");
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");
        if( QUEX_NAME(Buffer_character_index_begin)(&buffer) == 0 ) break;
        buffer._input_p        = buffer._memory._front;
        buffer._lexeme_start_p = buffer._memory._front + 1;
        /**/
        QUEX_NAME(BufferFiller_load_backward)(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    filler->base.delete_self(&filler->base);
}


