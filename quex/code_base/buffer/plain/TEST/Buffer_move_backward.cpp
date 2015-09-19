#include <quex/code_base/buffer/TESTS/Buffer_test_common.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Backward (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }


    QUEX_NAME(Buffer)         buffer;
    FILE*                     fh = prepare_input(); /* Festgemauert ... */
    ByteLoader*               byte_loader = ByteLoader_FILE_new(fh);
    QUEX_NAME(BufferFiller*)  filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    const size_t              StepSize = atoi(argv[1]);
    const size_t              MemorySize = 5;

    QUEX_TYPE_CHARACTER  memory[MemorySize];

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, E_Ownership_EXTERNAL);

    /* Read until the end of file is reached and set the _read_p to EOF */
    while( 1 + 1 == 2 ) {
        buffer._read_p        = QUEX_NAME(Buffer_text_end)(&buffer);
        buffer._lexeme_start_p = buffer._read_p;
        if( buffer._read_p == buffer.input.end_p ) break;
        QUEX_NAME(BufferFiller_load_forward)(&buffer);
    }
    test_move_backward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

