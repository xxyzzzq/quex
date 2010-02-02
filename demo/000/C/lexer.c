#include "tiny_lexer"
#include "tiny_lexer-token.i"

int 
main(int argc, char** argv) 
{        
    Token        token;
    tiny_lexer   qlex;
    int          token_n = 0;

    QUEX_FUNC(construct_file_name)(&qlex, "example.txt", 0x0, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    /* Loop until the 'termination' token arrives */
    token_n = 0;
    do {
        /* Get next token from the token stream   */
        QUEX_FUNC(receive_p)(&qlex, &token);
        /* Print out token information            */
        ++token_n;
        /* Check against 'termination'            */
    } while( token._id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
