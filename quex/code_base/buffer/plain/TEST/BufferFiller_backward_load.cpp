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
               sizeof(QUEX_CHARACTER_TYPE), (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    FILE*                         fh = prepare_input();
    QuexBuffer                    buffer;
    QuexBufferFiller_Plain<FILE>  filler;
    QUEX_CHARACTER_TYPE           memory[12];

    fseek(fh, 15 * sizeof(QUEX_CHARACTER_TYPE), SEEK_SET); 

    QuexBufferFiller_Plain_init(&filler, fh);
    QuexBuffer_init(&buffer, memory, 12, (QuexBufferFiller*)&filler);

    /* Simulate, as if we started at 0, and now reached '15' */
    buffer._content_first_character_index = 15;
    filler.start_position                 = 0;


    
    do {
        printf("------------------------------------------------------------\n");
        QuexBuffer_show_byte_content(&buffer, 5);
        printf("     ");
        QuexBuffer_show_content(&buffer);
        printf("\n");
        if( buffer._content_first_character_index == 0 ) break;
        buffer._input_p        = buffer._memory._front;
        buffer._lexeme_start_p = buffer._memory._front + 1;
        /**/
        QuexBufferFiller_load_backward(&buffer);
        printf("\n");
    } while( 1 + 1 == 2 );

    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}


