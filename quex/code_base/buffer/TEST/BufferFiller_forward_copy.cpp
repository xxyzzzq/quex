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
        printf("Forward: Copy Region;\n");
        printf("CHOICES: LS>C, LS=0, LS=4, LS=5, L=11;\n");
        return 0;
    }

    using namespace quex;

    QuexBuffer           buffer;
    QuexBufferFiller     filler;
    QUEX_CHARACTER_TYPE  content[] =  "0987654321"; 
    QUEX_CHARACTER_TYPE  memory[]  = "|----------|"; 
    int                  memory_size  = strlen((char*)memory);
    size_t               distance_i_l = 0;
    size_t               fallback_n   = 0;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);
    stderr = stdout;

    printf("## NOTE: This is only about copying, not about pointer adaptions!\n");

    QuexBuffer_init(&buffer, memory, memory_size, &filler);

    int s=0;
    if     ( cl_has(argc, argv, "LS=0") )   s = 0; 
    else if( cl_has(argc, argv, "LS=4") )   s = 4;
    else if( cl_has(argc, argv, "LS=5") )   s = 5;
    else if( cl_has(argc, argv, "LS=6") )   s = 6;
    else if( cl_has(argc, argv, "LS=10") )  s = 10;

    buffer._lexeme_start_p = buffer._memory._front + 1 + s;


    /* We want to observe the standard error output in HWUT, so redirect to stdout */
    for(buffer._input_p = buffer._lexeme_start_p; 
        buffer._input_p <= buffer._memory._back + 1; 
        ++(buffer._input_p) ) { 

        printf("------------------------------\n");
        printf("C - S = %i\n", (int)(buffer._input_p - buffer._lexeme_start_p));
        /**/
        memcpy((char*)(memory+1), (char*)content, strlen((char*)content));
        BufferFiller_show_content(&buffer);

        distance_i_l = buffer._input_p - buffer._lexeme_start_p;
        fallback_n   = __QuexBufferFiller_forward_copy_fallback_region(&buffer, distance_i_l);
        BufferFiller_show_content(&buffer);
    }
}
