#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include "test-helper.h"


int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_CHARACTER_TYPE));
        return 0;
    }

    QuexBuffer                    buffer;
    QuexBufferFiller_Plain<FILE>  filler;
    FILE*                         fh = prepare_input(); /* Festgemauert ... */
    size_t         SeekIndices[] = { 5, 9, 3, 8, 2, 15, 25, 7, 19, 4, 6, 20, 11, 0, 
                                     23, 18, 12, 21, 17, 27, 16, 26, 14, 24, 10, 13, 1, 22, 999 };

    QuexBufferFiller_Plain_init(&filler, fh);
    QuexBuffer_init(&buffer, 5, (QuexBufferFiller*)&filler);

    test_seek_and_tell(&buffer, SeekIndices);
    fclose(fh); /* this deletes the temporary file (see description of 'tmpfile()') */
}
