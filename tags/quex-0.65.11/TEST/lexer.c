#include "Simple.h"

#ifndef    CHARACTER_ENCODING_NAME 
#   define CHARACTER_ENCODING_NAME 0x0
#endif
#ifndef    PRINT_TOKEN_FIRST_NUMBER 
#   define PRINT_TOKEN_FIRST_NUMBER 0
#endif
#ifndef    TEST_EPILOG
#   define TEST_EPILOG \
    printf("| [END] number of token = %li\n", token_n); \
    printf("`------------------------------------------------------------------------------------\n");
#endif

int 
main(int argc, char** argv) 
{        
#   ifdef PRINT_TOKEN
    const size_t BufferSize = 1024;
    char         buffer[1024];
#   endif
    quex_Token*   token_p = 0x0;
    long          token_n = 0;
    quex_Simple   qlex;
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    QUEX_TYPE_TOKEN_ID token_id = (QUEX_TYPE_TOKEN_ID)0x0;
#   endif
    const char*        file_name = argc > 1 ? argv[1] : "example.txt";
    QUEX_NAME(from_file_name)(&qlex, file_name, CHARACTER_ENCODING_NAME);

    printf(",------------------------------------------------------------------------------------\n");
    printf("| [START]\n");
    fflush(stdout);
    fflush(stderr);

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

#       ifdef PRINT_LINE_COLUMN_NUMBER
        printf("(%i, %i)  \t", (int)token_p->_line_n, (int)token_p->_column_n);
#       endif
        /* Print out token information            */
        fflush(stderr);
#       ifdef PRINT_TOKEN
        if( token_n >= PRINT_TOKEN_FIRST_NUMBER ) {
            printf("%s", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));
            printf("\n");
        }
#       else
        printf("%s", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        printf("\n");
#       endif
        fflush(stdout);

        ++token_n;
        /* Check against 'termination'            */
#   ifdef QUEX_OPTION_TOKEN_POLICY_SINGLE
    } while( token_id != QUEX_TKN_TERMINATION );
#   else
    } while( token_p->_id != QUEX_TKN_TERMINATION );
#   endif

    TEST_EPILOG

    return 0;
}
