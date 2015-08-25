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

    QUEX_NAME(Buffer)         buffer;
    FILE*                     fh = prepare_input(); /* Festgemauert ... */
    ByteLoader*               byte_loader = ByteLoader_FILE_new(fh);
    QUEX_NAME(BufferFiller*)  filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    const size_t              StepSize = atoi(argv[1]);
    const size_t              MemorySize = 5;

    QUEX_NAME(Buffer_construct)(&buffer, filler, MemorySize); 

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

