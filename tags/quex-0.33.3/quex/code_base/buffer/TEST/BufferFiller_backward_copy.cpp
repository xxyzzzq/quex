#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <string.h>

int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Backward: Copy Region (BPC=%i);\n", sizeof(QUEX_CHARACTER_TYPE));
        printf("CHOICES:  Normal, StartOfStream;\n");
        return 0;
    }

    using namespace quex;

    QuexBuffer           buffer;
    QUEX_CHARACTER_TYPE  content[] =      { '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'} ; 
    QUEX_CHARACTER_TYPE  memory[]  = { '|', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '|'}; 
    int                  memory_size  = 12;
    size_t               fallback_n   = 0;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    stderr = stdout;

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");
    printf("## NOTE: When copying backward, it can be assumed: _input_p = _memory._front\n");

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QuexBuffer_init(&buffer, memory_size, 0x0);
    QuexBufferMemory_init(&buffer._memory, memory, memory_size);

    buffer._input_p = buffer._memory._front;
    if( cl_has(argc, argv, "Normal") ) 
        buffer._content_first_character_index = memory_size + 1; /* load backward possible */
    else                               
        buffer._content_first_character_index = 0;               /* impossible, start of stream */

    /* We want to observe the standard error output in HWUT, so redirect to stdout */
    for(buffer._lexeme_start_p = buffer._memory._front + 1; 
        buffer._lexeme_start_p != buffer._memory._back; 
        ++(buffer._lexeme_start_p) ) { 

        memcpy((char*)(memory+1), (char*)content, (memory_size-2)*sizeof(QUEX_CHARACTER_TYPE));
        /**/
        printf("------------------------------\n");
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front),
               (char)*buffer._lexeme_start_p);
        /**/
        QuexBuffer_show_content(&buffer);
        printf("\n");

        if( buffer._lexeme_start_p - buffer._input_p == memory_size - 2 ) 
            printf("##NOTE: The following break up is intended\n##");
        fallback_n   = __QuexBufferFiller_backward_copy_backup_region(&buffer);
        QuexBuffer_show_content(&buffer);
        printf("\n");
    }
}
