#include <BufferFiller>
#include <BufferFiller.i>
#include <Buffer_debug.i>
#include <string.h>

int cl_has(int argc, char* arg, const char* What)
{
    return argc > 1 && strcmp(arg, What) == 0;
     
}

int
main(int argc, char** argv)
{
    using namespace quex;

    QuexBuffer        buffer
    QuexBufferFiller  filler;

    if( cl_has(argc, argv[1], "--hwut-info") ) {
        printf("Forward: Copy Region;\n");
        return 0;
    }

    filler.client = &buffer;

    QUEX_CHARACTER_TYPE  memory[10];
    int                  memory_size = 10;

    QuexBuffer_init(&buffer, memory, memory_size);

    gt

}
