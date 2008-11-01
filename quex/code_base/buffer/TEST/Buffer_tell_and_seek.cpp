#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/MemoryManager>
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
    size_t               SeekIndices[] = { 11, 8, 9, 10, 4, 5, 12, 3, 0, 1, 2, 6, 7,};
    size_t*              SeekIndicesEnd = SeekIndicesEnd + sizeof(SeekIndices) / sizeof(size_t);
    QUEX_CHARACTER_TYPE  content[]     = { '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'} ; 
    QUEX_CHARACTER_TYPE  memory[]      = { '|', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '|'}; 
    int                  memory_size   = 12;
    size_t               fallback_n    = 0;

    assert(QUEX_SETTING_BUFFER_MIN_FALLBACK_N == 5);

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QuexBuffer_init(&buffer, memory_size, 0x0);
    QuexBuffer_setup_memory(&buffer, memory, memory_size);

    buffer._input_p = buffer._memory._front + 1;

    printf("input_p      = %i (--> '%c')\t", 
           (int)(buffer._input_p - buffer._memory._front - 1), (char)*buffer._input_p);
    printf("lexeme start = %i (--> '%c')\n", 
           (int)(buffer._lexeme_start_p - buffer._memory._front - 1), (char)*buffer._lexeme_start_p);
    for(size_t* it = SeekIndices; it != SeekIndicesEnd; ++it) {
        /**/
        printf("------------------------------\n");
        /**/
        printf("SEEK --> %i\n", (int)*it);
        QuexBuffer_seek(&buffer, *it);
        printf("input_p      = %i (--> '%c')\t", 
               (int)(buffer._input_p - buffer._memory._front - 1),
               (char)*buffer._input_p);
        printf("lexeme start = %i (--> '%c')\n", 
               (int)(buffer._lexeme_start_p - buffer._memory._front - 1),
               (char)*buffer._lexeme_start_p);
        printf("TELL:    %i", (int)QuexBuffer_tell(&buffer));
        printf("\n");
    }
}
