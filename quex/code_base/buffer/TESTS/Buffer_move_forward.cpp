#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include <quex/code_base/single.i>

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Move by Offset: Forward (BPC=%i);\n", sizeof(QUEX_TYPE_LEXATOM));
        printf("CHOICES:  1, 2, 3, 4, 5;\n");
        return 0;
    }
    if( argc == 1 ) {
        printf("Command line argument required.\n");
        return 0;
    }


    QUEX_NAME(Buffer)    buffer;
    int                  memory_size   = 12;
    const size_t         StepSize      = atoi(argv[1]);

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    QUEX_TYPE_LEXATOM  memory[memory_size];
    QUEX_NAME(Buffer_construct)(&buffer, (QUEX_NAME(LexatomLoader)*)0x0, 
                                &memory[0], memory_size, &memory[memory_size], E_Ownership_EXTERNAL);

    for(int i = 1; i < memory_size - 2 ; ++i) *(buffer._memory._front + i) = '0' + i;
    *(buffer._memory._back - 1) = '0';

    test_move_forward(&buffer, StepSize);

}
