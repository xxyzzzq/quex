#include <stdio.h>

#include "Simple.h"

int 
main(int argc, char** argv) 
{        
    Simple  qlex;
    uint8_t buffer[4711];
    size_t  BufferSize = 4711;

    QUEX_NAME(construct_memory)(&qlex, 
                                buffer, BufferSize, buffer + 1, 
                                0x0, false);

    printf("Buffer Size: %i\n",
           (int)QUEX_NAME(buffer_fill_region_size)(&qlex));


    QUEX_NAME(destruct)(&qlex);
    return 0;
}

