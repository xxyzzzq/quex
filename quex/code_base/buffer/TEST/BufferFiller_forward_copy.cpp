#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <string.h>

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Forward: Copy Fallback Region (BPC=%i);\n", sizeof(QUEX_CHARACTER_TYPE));
        return 0;
    }

    using namespace quex;

    QuexBuffer           buffer;
    QUEX_CHARACTER_TYPE  content[]    = { '0', '9', '8', '7', '6', '5', '4', '3', '2', '1' }; 
    int                  memory_size  = 12;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    stderr = stdout;

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");
    printf("## NOTE: FallbackN = %i!\n", QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
    printf("## NOTE: When copying, it can be assumed that the _input_p stands on _memory._back\n");

    /* Filler = 0x0, otherwise, buffer would start loading content */
    buffer.filler = 0x0;
    QuexBuffer_construct_wo_filler(&buffer, memory_size, 0, 0);

    buffer._input_p = buffer._memory._back;

    /* We want to observe the standard error output in HWUT, so redirect to stdout */
    for(buffer._lexeme_start_p = buffer._memory._back; 
        buffer._lexeme_start_p != buffer._memory._front; 
        --(buffer._lexeme_start_p) ) { 

        memcpy((void*)(buffer._memory._front + 1), (void*)content, (memory_size-2)*sizeof(QUEX_CHARACTER_TYPE));
        /**/
        printf("------------------------------\n");
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front),
               (char)*buffer._lexeme_start_p);
        /**/
        QuexBuffer_show_content(&buffer);
        printf("\n");

        const size_t  DistanceIL = buffer._input_p - buffer._lexeme_start_p;
        if( buffer._input_p - buffer._lexeme_start_p == memory_size - 2 ) 
            printf("##NOTE: The following break up is intended\n##");

        const size_t  FallBackN = __QuexBufferFiller_forward_compute_fallback_region(&buffer, DistanceIL);
        __QuexBufferFiller_forward_copy_fallback_region(&buffer, FallBackN);
        QuexBuffer_show_content(&buffer);
        printf("\n");
    }
}
