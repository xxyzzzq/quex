#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/converter_helper/unicode.i>
#include <cstring>

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Backward: Copy Region (BPC=%i);\n", sizeof(QUEX_TYPE_CHARACTER));
        printf("CHOICES:  Normal, StartOfStream;\n");
        return 0;
    }
    if( argc == 1 ) {
        printf("Command line argument required.\n");
        return 0;
    }

    using namespace quex;

    QUEX_NAME(Buffer)           buffer;
    QUEX_TYPE_CHARACTER  content[]   = { '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}; 
    int                  memory_size = sizeof(content) / sizeof(QUEX_TYPE_CHARACTER) + 2;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    /* We want to observe the standard error output in HWUT, so redirect to stdout */
    stderr = stdout;

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QUEX_NAME(Buffer_construct)(&buffer, (void*)0x0, 0x0, memory_size, 0x0, 0x0, 0, false);
    QUEX_NAME(Buffer_end_of_file_unset)(&buffer);

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");
    printf("## NOTE: When copying backward, it can be assumed: _input_p = _memory._front\n");

    buffer._input_p = buffer._memory._front;

    if( cl_has(argc, argv, "Normal") ) {
        buffer._content_character_index_begin = memory_size + 1; /* load backward possible      */
        buffer._content_character_index_end   = 2 * memory_size - 1; 
    } else {                              
        buffer._content_character_index_begin = 0;               /* impossible, start of stream */
        buffer._content_character_index_end   = memory_size - 2; /* impossible, start of stream */
    }

    for(buffer._lexeme_start_p = buffer._memory._front + 1; 
        buffer._lexeme_start_p != buffer._memory._back; 
        ++(buffer._lexeme_start_p) ) { 

        memcpy((char*)(buffer._memory._front+1), (char*)content, (memory_size-2)*sizeof(QUEX_TYPE_CHARACTER));
        QUEX_NAME(Buffer_end_of_file_set)(&buffer, buffer._memory._back);
        /**/
        printf("------------------------------\n");
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front),
               (char)*buffer._lexeme_start_p);
        /**/
        QUEX_NAME(Buffer_show_content)(&buffer);
        printf("\n");

        if( buffer._lexeme_start_p - buffer._input_p == memory_size - 2 ) 
            printf("##NOTE: The following break up is intended\n##");
        if( buffer._content_character_index_begin != 0 ) {
            const size_t  BackwardDistance = QUEX_NAME(__BufferFiller_backward_compute_backward_distance)(&buffer);
            QUEX_NAME(__BufferFiller_backward_copy_backup_region)(&buffer, BackwardDistance);
        }
        QUEX_NAME(Buffer_show_content)(&buffer);
        printf("\n");
    }
}
