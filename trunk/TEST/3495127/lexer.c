#include "Simple.h"

#ifndef    CHARACTER_ENCODING_NAME 
#   define CHARACTER_ENCODING_NAME 0x0
#endif

int 
main(int argc, char** argv) 
{        
#   ifdef PRINT_TOKEN
    const size_t BufferSize = 1024;
    char         buffer[1024];
#   endif
    QUEX_TYPE_TOKEN*   token_p = 0x0;
    int                token_n = 0;
    quex_Simple        qlex;
    const char*        file_name = argc > 1 ? argv[1] : "example.txt";
    QUEX_NAME(construct_file_name)(&qlex, file_name, CHARACTER_ENCODING_NAME, false);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");
    fflush(stdout);
    fflush(stderr);

    /* Loop until the 'termination' token arrives */
    token_n = 0;

    do {
        /* Get next token from the token stream   */
        QUEX_NAME(receive)(&qlex, &token_p);
        printf("(%i, %i)  \t", (int)token_p->_line_n, (int)token_p->_column_n);
        /* Print out token information            */
        fflush(stderr);
        printf("%s: ", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        switch( token_p->_id ) {
        case QUEX_TKN_ON_AFTER_MATCH:
        case QUEX_TKN_ON_MATCH______:
            printf("%i\n", (int)token_p->number); 
            break;
        default:
            printf("%s\n", QUEX_NAME_TOKEN(pretty_char_text)(token_p, buffer, BufferSize)); 
            break;
        }
        fflush(stdout);

        ++token_n;
        /* Check against 'termination'            */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", token_n);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
