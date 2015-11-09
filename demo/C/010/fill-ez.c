#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

size_t 
messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER*, size_t);

int 
main(int argc, char** argv) 
{        
    quex_Token       token;
    quex_tiny_lexer  qlex;
    size_t           receive_n = (size_t)-1;
    size_t           BufferSize = 1024;
    char             buffer[1024];
    bool             out_f = false;
    QUEX_TYPE_CHARACTER* begin_p;
    QUEX_TYPE_CHARACTER* end_p;

    quex_tiny_lexer_from_ByteLoader(&qlex, (ByteLoader*)0, 0);
    QUEX_NAME_TOKEN(construct)(&token);

    (void)QUEX_NAME(token_p_swap)(&qlex, &token);
    while( 1 + 1 == 2 ) {
        /* -- Initialize the filling of the fill region         */
        qlex.buffer.fill_prepare(&qlex.buffer, (void**)&begin_p, (const void**)&end_p);

        /* -- Call the low lever driver to fill the fill region */
        receive_n = messaging_framework_receive_into_buffer_syntax_chunk(begin_p, 
                                                                         (end_p - begin_p)*sizeof(QUEX_TYPE_CHARACTER)); 

        /* -- Inform the buffer about the number of loaded characters NOT NUMBER OF BYTES! */
        qlex.buffer.fill_finish(&qlex.buffer, &begin_p[receive_n]);

        /* -- Loop until the 'termination' token arrives */
        while( 1 + 1 == 2 ) {
            const QUEX_TYPE_TOKEN_ID TokenID = QUEX_NAME(receive)(&qlex);

            if( TokenID == QUEX_TKN_TERMINATION ) break;
            if( TokenID == QUEX_TKN_BYE )         { out_f = true; break; }

            printf("Consider: %s \n", QUEX_NAME_TOKEN(get_string)(&token, buffer, BufferSize));
        }
        if( out_f ) break;
    }

    QUEX_NAME(destruct)(&qlex);
    QUEX_NAME_TOKEN(destruct)(&token);
    return 0;
}

