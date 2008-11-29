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
    QUEX_CHARACTER_TYPE  memory[]      = { '|', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '|'}; 
    int                  memory_size   = 12;
    size_t               fallback_n    = 0;
    const size_t         StepSize      = atoi(argv[1]);

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QuexBuffer_init(&buffer, memory_size, 0x0);
    QuexBuffer_setup_memory(&buffer, memory, memory_size);

    buffer._input_p = buffer._memory._back - 1;

    test_move_backward(&buffer, StepSize);
}
