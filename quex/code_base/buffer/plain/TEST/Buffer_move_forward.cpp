#include <quex/code_base/buffer/TEST/Buffer_test_common.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Forward (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }

    QUEX_NAME(Buffer)  buffer;
    const size_t       StepSize = atoi(argv[1]);
    FILE*              fh       = prepare_input(); /* Festgemauert ... */

    const size_t       MemorySize = 5;
    ByteLoader*        byte_loader = ByteLoader_FILE_new(fh);

    QUEX_NAME(Buffer_construct)(&buffer, 
                                QUEX_NAME(BufferFiller_new)(byte_loader, QUEX_TYPE_BUFFER_FILLER_PLAIN, 0, 0), 
                                0x0, MemorySize, 0, false);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

