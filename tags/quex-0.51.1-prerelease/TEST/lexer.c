#include "Simple"
#include "Simple-token.i"

int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN*   token_p = 0x0;
    int                token_n = 0;
    Simple             qlex;

    QUEX_NAME(construct_file_name)(&qlex, "example.txt", 0x0, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    /* Loop until the 'termination' token arrives */
    token_n = 0;
    do {
        /* Get next token from the token stream   */
        QUEX_NAME(receive)(&qlex, &token_p);
        /* Print out token information            */
        printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        ++token_n;
        /* Check against 'termination'            */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
