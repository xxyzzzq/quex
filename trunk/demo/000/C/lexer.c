#include "tiny_lexer"

int 
main(int argc, char** argv) 
{        
    Token        Token;
    tiny_lexer   qlex;
    int          token_n = 0;

    QUEX_FUNC(construct_file_name)(&qlex, "example.txt", 0x0, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    /* Loop until the 'termination' token arrives */
    token_n = 0;
    do {
        /* Get next token from the token stream   */
        QUEX_FUNC(receive)(&qlex, &Token);
        /* Print out token information            */
        ++token_n;
        /* Check against 'termination'            */
    } while( Token.type_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
