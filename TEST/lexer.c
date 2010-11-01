#include "Simple.h"

int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN*   token_p = 0x0;
    int                token_n = 0;
    Simple             qlex;
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    QUEX_TYPE_TOKEN_ID token_id = (QUEX_TYPE_TOKEN_ID)0x0;
#   endif
    const char*        file_name = argc > 1 ? argv[1] : "example.txt";
    QUEX_NAME(construct_file_name)(&qlex, file_name, 0x0, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    /* Loop until the 'termination' token arrives */
    token_n = 0;

#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    token_p = QUEX_NAME(token_p)(&qlex);
#   endif

    do {
        /* Get next token from the token stream   */
#       ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
        token_id = QUEX_NAME(receive)(&qlex);
#       else
        QUEX_NAME(receive)(&qlex, &token_p);
#       endif
        /* Print out token information            */
        printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        ++token_n;
        /* Check against 'termination'            */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
