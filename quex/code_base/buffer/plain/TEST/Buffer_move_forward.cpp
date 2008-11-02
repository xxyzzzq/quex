#include <quex/code_base/buffer/TEST/Buffer_test_common.i>

#include "test-helper.h"

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Forward (BPC=%i);\n", sizeof(QUEX_CHARACTER_TYPE));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }


    QuexBuffer           buffer;
    QUEX_CHARACTER_TYPE  memory[]      = { '|', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '|'}; 
    int                  memory_size   = 12;
    size_t               fallback_n    = 0;
    const size_t         StepSize      = atoi(argv[1]);

    FILE*                         fh = prepare_input(); /* Festgemauert ... */
    QuexBufferFiller_Plain<FILE>  filler;

    QuexBufferFiller_Plain_init(&filler, fh);
    QuexBuffer_init(&buffer, 5, (QuexBufferFiller*)&filler);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

