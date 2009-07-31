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
        printf("Load Forward: Character=%i Byte(s), Fallback=%i\n", 
               sizeof(QUEX_TYPE_CHARACTER), (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    FILE*                         fh = prepare_input();
    QuexBuffer                    buffer;

    QuexBuffer_construct(&buffer, fh, 0x0, /* BufferMemorySize */ 8, 0x0, 0);

    do {
        printf("------------------------------------------------------------\n");
        QuexBuffer_show_byte_content(&buffer, 5);
        printf("     ");
        QuexBuffer_show_content(&buffer);
        printf("\n");
        if( buffer._memory._end_of_file_p != 0x0 ) break;
        buffer._input_p        = buffer._memory._back;
        buffer._lexeme_start_p = buffer._memory._back;
        /**/
        QuexBufferFiller_load_forward(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

