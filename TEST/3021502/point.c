#include <stdio.h>

#include "Simple.h"

int 
main(int argc, char** argv) 
{        
    quex_Simple  qlex;
    uint8_t      buffer[4711];
    size_t       BufferSize = 4711;

    QUEX_NAME(from_memory)(&qlex, 
                           buffer, BufferSize, buffer + 1); 

    printf("Buffer Size: %i\n",
           (int)(qlex.buffer.input.end_p - qlex.buffer._memory._front[1])); 


    QUEX_NAME(destruct)(&qlex);
    return 0;
}

