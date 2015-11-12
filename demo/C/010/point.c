#include <stdio.h>

#include "tiny_lexer.h"
#include "messaging-framework.h"

/* #include <quex/code_base/buffer/Buffer_debug> */

int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN    token;
    quex_tiny_lexer    qlex;
    size_t             BufferSize = 1024;
    char               buffer[1024];
    size_t             receive_n = (size_t)-1;
    int                i = 0;

    if( QUEX_SETTING_BUFFER_MIN_FALLBACK_N != 0 ) {
        QUEX_ERROR_EXIT("This method fails if QUEX_SETTING_BUFFER_MIN_FALLBACK_N != 0\n"
                        "Consider using the method described in 're-point.c'.");
    }

    QUEX_NAME_TOKEN(construct)(&token);

    receive_n = receiver_fill_to_internal_buffer();

    QUEX_NAME(from_memory)(&qlex, 
                           MESSAGING_FRAMEWORK_BUFFER, 
                           MESSAGING_FRAMEWORK_BUFFER_SIZE,
                           &MESSAGING_FRAMEWORK_BUFFER[receive_n]);

    /* Iterate 3 times doing the same thing in order to illustrate
     * the repeated activation of the same chunk of memory. */
    for(i = 0; i < 3; ++i ) {
        /* -- Loop until the 'termination' token arrives */
        QUEX_NAME(token_p_swap)(&qlex, &token); 

        do {
            QUEX_NAME(receive)(&qlex);
            

            if( token._id != QUEX_TKN_TERMINATION )
                printf("Consider: %s \n", QUEX_NAME_TOKEN(get_string)(&token, buffer, BufferSize));

            if( token._id == QUEX_TKN_BYE ) 
                printf("##\n");

        } while( token._id != QUEX_TKN_TERMINATION );

        QUEX_NAME(reset_memory)(&qlex,
                                MESSAGING_FRAMEWORK_BUFFER, 
                                MESSAGING_FRAMEWORK_BUFFER_SIZE,
                                &MESSAGING_FRAMEWORK_BUFFER[receive_n]);
    }

    QUEX_NAME(token_p_swap)(&qlex, (QUEX_TYPE_TOKEN*)0); /* Avoid destruction of my token. */
    QUEX_NAME(destruct)(&qlex);
    QUEX_NAME_TOKEN(destruct)(&token);
    return 0;
}

