#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    using namespace quex;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Load Forward: Character=%i Byte(s), Fallback=%i\n", 
               sizeof(QUEX_CHARACTER_TYPE), (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    FILE*                         fh = prepare_input();
    QuexBuffer                    buffer;
    QuexBufferFiller_Plain<FILE>  filler;
    QUEX_CHARACTER_TYPE           memory[8];

    QuexBufferFiller_Plain_init(&filler, fh);
    QuexBuffer_init(&buffer, memory, 8, (QuexBufferFiller*)&filler);

    
    do {
        printf("------------------------------------------------------------\n");
        QuexBuffer_show_byte_content(&buffer, 5);
        printf("     ");
        QuexBuffer_show_content(&buffer);
        printf("\n");
        if( buffer._end_of_file_p != 0x0 ) break;
        buffer._input_p        = buffer._memory._back;
        buffer._lexeme_start_p = buffer._memory._back;
        /**/
        QuexBufferFiller_load_forward(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

