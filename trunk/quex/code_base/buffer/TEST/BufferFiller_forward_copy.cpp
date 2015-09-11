#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/BufferFiller>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/single.i>
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
    const int            memory_size  = 12;
    QUEX_TYPE_CHARACTER  memory[memory_size];

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    stderr = stdout;

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QUEX_NAME(Buffer_construct)(&buffer, 
                                (QUEX_NAME(BufferFiller)*)0x0, 
                                &memory[0], memory_size, 0,
                                E_Ownership_EXTERNAL);
    QUEX_NAME(Buffer_end_of_file_unset)(&buffer);

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");
    printf("## NOTE: FallbackN = %i!\n", QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
    printf("## NOTE: When copying, it can be assumed that the _input_p stands on _memory._back\n");
    buffer._input_p = buffer._memory._back;
    printf("## NOTE: And the end of file has not been reached yet.\n");
    buffer._memory._end_of_file_p = 0x0;

    for(buffer._lexeme_start_p = buffer._memory._back; 
        buffer._lexeme_start_p != buffer._memory._front; 
        --(buffer._lexeme_start_p) ) { 

        memset(&buffer._memory._front[1], (QUEX_TYPE_CHARACTER)-1, sizeof(memory)/sizeof(memory[0])-2);
        memcpy(&buffer._memory._front[1], (void*)content, sizeof(content));
        buffer._content_character_index_end = sizeof(content) / sizeof(content[0]);

        /**/
        printf("------------------------------\n");
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front),
               (char)*buffer._lexeme_start_p);
        /**/
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");

        if( buffer._input_p - buffer._lexeme_start_p == memory_size - 2 ) 
            printf("##NOTE: The following break up is intended\n##");

        QUEX_NAME(Buffer_move_away_passed_content)(&buffer);
        QUEX_NAME(Buffer_show_content_intern)(&buffer);
        printf("\n");
    }
}
