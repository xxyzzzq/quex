#include <stdio.h>

#include "tiny_lexer"
#include "tiny_lexer-token.i"
#include "messaging-framework.h"

int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN*   token;
    tiny_lexer         qlex;
    size_t             BufferSize = 1024;
    char               buffer[1024];

    QUEX_NAME(construct_memory)(&qlex, MESSAGING_FRAMEWORK_BUFFER, MESSAGING_FRAMEWORK_BUFFER_SIZE, 0x0, false);

    // -- Call the low lever driver to fill the fill region
    size_t receive_n = messaging_framework_receive_to_internal_buffer();

    // -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES!
    QUEX_NAME(buffer_fill_region_finish)(&qlex, receive_n-1);

    // -- Loop until the 'termination' token arrives
    token = QUEX_NAME(token_p)(&qlex);
    do {
        QUEX_NAME(receive)(&qlex);

        if( token->_id == QUEX_TKN_BYE ) 
            printf("## ");

        if( token->_id != QUEX_TKN_TERMINATION )
        printf("Consider: %s\n", QUEX_NAME_TOKEN(get_string)(token, buffer, BufferSize));
        
    } while( token->_id != QUEX_TKN_TERMINATION );

    return 0;
}

