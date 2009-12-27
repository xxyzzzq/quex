#include "tiny_lexer"

int 
main(int argc, char** argv) 
{        
    Token        Token;
    tiny_lexer   qlex;

    tiny_lexer_construct(&qlex, "example.txt");

    fprintf(",------------------------------------------------------------------------------------\n");
    fprintf("| [START]\n");

    int number_of_tokens = 0;
    /* Loop until the 'termination' token arrives */
    do {
        /* Get next token from the token stream   */
        QUEX_FUNC(receive)(&qlex, &Token);
        /* Print out token information            */
        ++number_of_tokens;
        /* Check against 'termination'            */
    } while( Token.type_id != QUEX_TKN_TERMINATION );

    fprintf("| [END] number of token = %i\n", number_of_tokens);
    fprintf("`------------------------------------------------------------------------------------\n");

    return 0;
}
