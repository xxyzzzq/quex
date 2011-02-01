#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/converter_helper/unicode.i>
#include <string.h>

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Forward: Copy Fallback Region (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        return 0;
    }
    /* if( argc == 1 ) { printf("Command line argument required.\n"); return 0; } */

    using namespace quex;

    QUEX_NAME(Buffer)    buffer;
    QUEX_TYPE_CHARACTER  content[]    = { '0', '9', '8', '7', '6', '5', '4', '3', '2', '1' }; 
    int                  memory_size  = 12;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    stderr = stdout;

    /* Filler = 0x0, otherwise, buffer would start loading content */
    buffer.filler = 0x0;
    QUEX_NAME(Buffer_construct)(&buffer, (void*)0x0, 0x0, memory_size, 0x0, 0x0, 0, false);
    QUEX_NAME(Buffer_end_of_file_unset)(&buffer);

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");
    printf("## NOTE: FallbackN = %i!\n", QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
    printf("## NOTE: When copying, it can be assumed that the _input_p stands on _memory._back\n");
    buffer._input_p = buffer._memory._back;
    printf("## NOTE: And the end of file has not been reached yet.\n");
    buffer._memory._end_of_file_p = 0x0;

    /* We want to observe the standard error output in HWUT, so redirect to stdout */
    for(buffer._lexeme_start_p = buffer._memory._back; 
        buffer._lexeme_start_p != buffer._memory._front; 
        --(buffer._lexeme_start_p) ) { 

        memcpy((void*)(buffer._memory._front + 1), (void*)content, (memory_size-2)*sizeof(QUEX_TYPE_CHARACTER));
        /**/
        printf("------------------------------\n");
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front),
               (char)*buffer._lexeme_start_p);
        /**/
        QUEX_NAME(Buffer_show_content)(&buffer);
        printf("\n");

        const size_t  DistanceIL = buffer._input_p - buffer._lexeme_start_p;
        if( buffer._input_p - buffer._lexeme_start_p == memory_size - 2 ) 
            printf("##NOTE: The following break up is intended\n##");

        const size_t  FallBackN = QUEX_NAME(__BufferFiller_forward_compute_fallback_region)(&buffer, DistanceIL);
        QUEX_NAME(__BufferFiller_forward_copy_fallback_region)(&buffer, FallBackN);
        QUEX_NAME(Buffer_show_content)(&buffer);
        printf("\n");
    }
}
