/* -*- C++ -*- vim: set syntax=cpp:
 */
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/buffer/BufferFiller.i>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <string.h>

using namespace quex;

inline int 
cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

inline void 
print_this(QuexBuffer* buffer)
{
    printf("input_p      = %i (--> '%c')\t", 
           (int)(buffer->_input_p - buffer->_memory._front - 1), (char)*buffer->_input_p);
    printf("lexeme start = %i (--> '%c')\n", 
           (int)(buffer->_lexeme_start_p - buffer->_memory._front - 1), (char)*buffer->_lexeme_start_p);
}

inline void 
test_move_backward(QuexBuffer* buffer, const size_t StepSize)
{
    print_this(buffer);
    while( buffer->_input_p != buffer->_memory._front + 1 ) {
        QuexBuffer_move_backward(buffer, StepSize);
        print_this(buffer);
    }
    QuexBuffer_move_backward(buffer, StepSize);
    print_this(buffer);
}

inline void 
test_move_forward(QuexBuffer* buffer, size_t StepSize)
{
    print_this(buffer);
    while( QuexBuffer_distance_input_to_text_end(buffer) != 0 ) {
        QuexBuffer_move_forward(buffer, StepSize);
        print_this(buffer);
    }
    QuexBuffer_move_forward(buffer, StepSize);
    print_this(buffer);
}

inline void 
test_seek_and_tell(QuexBuffer* buffer)
{
    size_t  SeekIndices[] = { 11, 8, 9, 10, 4, 5, 12, 3, 0, 1, 2, 6, 7, 999 };

    print_this(buffer);
    for(size_t* it = SeekIndices; *it != 999; ++it) {
        /**/
        printf("------------------------------\n");
        /**/
        printf("SEEK --> %i\n", (int)*it);
        QuexBuffer_seek(buffer, *it);
        print_this(buffer);
        printf("TELL:    %i", (int)QuexBuffer_tell(buffer));
        printf("\n");
    }
}

