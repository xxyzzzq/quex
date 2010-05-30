#include<stdio.h>    

#include "EasyLexer"
#include "EasyLexer-token.i"


#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

int 
main(int argc, char** argv) 
{        
    Token*     token_p = 0x0;
    size_t     token_n = 0;
    EasyLexer  qlex;

    QUEX_NAME(construct_file_name)(&qlex, "example.txt", ENCODING_NAME, false);
    /* Alternatives:
     * QUEX_NAME(construct_memory)(&qlex, MemoryBegin, MemorySize,
     *                             CharacterEncodingName (default 0x0),
     *                             ByteOrderReversionF   (default false));
     * QUEX_NAME(construct_FILE)(&qlex, FILE_handle, 
     *                           CharacterEncodingName (default 0x0),
     *                           ByteOrderReversionF   (default false)); */
    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");

    /* Loop until the 'termination' token arrives */
    do {
        /* Get next token from the token stream   */
        token_p = QUEX_NAME(receive)(&qlex);
        /* Print out token information            */
        printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        ++token_n;
        /* Check against 'termination'            */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
