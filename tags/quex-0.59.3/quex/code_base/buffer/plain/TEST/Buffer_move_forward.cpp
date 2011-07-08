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

    QUEX_NAME(Buffer_construct)(&buffer, fh, 0x0, 5, 0x0, 0x0, 0, false);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

