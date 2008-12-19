#include <quex/code_base/buffer/TEST/Buffer_test_common.i>

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Backward (BPC=%i);\n", sizeof(QUEX_CHARACTER_TYPE));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }

    QuexBuffer           buffer;
    int                  memory_size   = 12;
    const size_t         StepSize      = atoi(argv[1]);

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    QuexBuffer_construct_wo_filler(&buffer, memory_size, 0, 0);

    for(int i = 1; i < memory_size - 2 ; ++i) *(buffer._memory._front + i) = '0' + i;
    *(buffer._memory._back - 1) = '0';

    buffer._input_p = buffer._memory._back - 1;

    test_move_backward(&buffer, StepSize);
}
