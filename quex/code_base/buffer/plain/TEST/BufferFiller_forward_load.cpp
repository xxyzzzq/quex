#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/plain/BufferFiller_Plain.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    using namespace quex;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Load Forward: Character=%i Byte(s), Fallback=%i\n", 
               sizeof(QUEX_TYPE_CHARACTER), (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    QUEX_NAME(Buffer)         buffer;
    FILE*                     fh          = prepare_input(); /* Festgemauert ... */
    ByteLoader*               byte_loader = ByteLoader_FILE_new(fh);
    QUEX_NAME(BufferFiller*)  filler      = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    const size_t              MemorySize  = 8;
    QUEX_TYPE_CHARACTER       memory[MemorySize];
    int                       count_n     = 0;

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, 
                                E_Ownership_EXTERNAL);

    do {
        printf("------------------------------------------------------------\n");
        QUEX_NAME(Buffer_show_byte_content)(&buffer, 5);
        printf("     ");
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");
        if( buffer.input.end_p ) break;
        buffer._read_p         = buffer._memory._back;
        buffer._lexeme_start_p = buffer._memory._back;
        /**/
        QUEX_NAME(BufferFiller_load_forward)(&buffer);
        printf("\n");
        if( ++count_n > 1000 ) {
            printf("Error: too many iterations.\n");
        }
    } while( 1 + 1 == 2 );

    filler->delete_self(filler);
}

