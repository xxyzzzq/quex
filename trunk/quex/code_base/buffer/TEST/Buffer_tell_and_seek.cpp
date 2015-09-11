#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/single.i>


int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }
    /* if( argc == 1 ) { printf("Command line argument required.\n"); return 0; } */

    QUEX_NAME(Buffer)    buffer;
    size_t               SeekIndices[] = { 11, 8, 9, 10, 4, 5, 12, 3, 0, 1, 2, 6, 7, 999 };
    int                  memory_size   = 12;
    QUEX_TYPE_CHARACTER  memory[memory_size];

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    for(int i = 1; i < memory_size - 1 ; ++i) memory[i] = '0' + i % 10;

    QUEX_NAME(Buffer_construct)(&buffer, 
                                (QUEX_NAME(BufferFiller)*)0x0, 
                                &memory[0], memory_size, &memory[memory_size-1], 
                                E_Ownership_EXTERNAL);

    test_seek_and_tell(&buffer, SeekIndices);
}
