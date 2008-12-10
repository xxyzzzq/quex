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
    const size_t         StepSize      = atoi(argv[1]);

    FILE*                         fh = prepare_input(); /* Festgemauert ... */
    QuexBufferFiller_Plain<FILE>  filler;

    QuexBufferFiller_Plain_init(&filler, fh);
    buffer.filler = (quex::__QuexBufferFiller_tag*)&filler;
    QuexBufferMemory_init(&(buffer._memory), MemoryManager_get_BufferMemory(5),5 );      
    QuexBuffer_init(&buffer, /* OnlyResetF */false);

    test_move_forward(&buffer, StepSize); 
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}

