#include <stdio.h>    

#include "EasyLexer.h"


int 
main(int argc, char** argv) 
{        
    quex_Token*    token_p = 0x0;
    quex_EasyLexer qlex;
    const size_t   BufferSize = 1024;
    char           buffer[1024];
    const char*    FileName = "example.txt";

    QUEX_NAME(from_file_name)(&qlex, FileName, (void*)0, false);

    do {
        QUEX_NAME(receive)(&qlex, &token_p);

        printf("%s \n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));

    } while( token_p->_id != QUEX_TKN_TERMINATION );

    QUEX_NAME(destruct)(&qlex);

    return 0;
}
