#include <quex/code_base/buffer/TEST/Buffer_test_common.i>


int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: Bytes Per Character (BPC)=%i;\n", sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }
    if( argc == 1 ) {
        printf("Command line argument required.\n");
        return 0;
    }

    QuexBuffer           buffer;
    size_t               SeekIndices[] = { 11, 8, 9, 10, 4, 5, 12, 3, 0, 1, 2, 6, 7, 999 };
    int                  memory_size   = 12;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    QuexBuffer_construct_wo_filler(&buffer, 0x0, memory_size);

    for(int i = 1; i < memory_size - 2 ; ++i) *(buffer._memory._front + i) = '0' + i;
    *(buffer._memory._back - 1) = '0';

    buffer._input_p = buffer._memory._front + 1;
    QuexBuffer_end_of_file_set(&buffer, buffer._memory._back);

    test_seek_and_tell(&buffer, SeekIndices);
}
