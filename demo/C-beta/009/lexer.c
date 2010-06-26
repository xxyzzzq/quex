#include <stdio.h>
#include <assert.h>

#include "tiny_lexer"
#include "tiny_lexer-token.i"

int 
main(int argc, char** argv) 
{        
    QUEX_TYPE_TOKEN*  token_p = 0x0;
    tiny_lexer        qlex;
    /**/
    int               number_of_tokens = 0;
    /**/
    const size_t      UTF8ContentSize = 1024;
    uint8_t           utf8_content[1024];
    uint8_t*          end = (uint8_t)0x0;


    /* Normal File Input */
    printf("## FILE* (stdio.h):\n");
    printf("##    Note this works only when engine is generated with -b 1 (or no -b)\n");
    printf("##    and therefore QUEX_TYPE_CHARACTER == uint8_t.\n");
    assert(sizeof(QUEX_TYPE_CHARACTER) == sizeof(uint8_t));
    QUEX_NAME(construct_file_name)(&qlex, "example.txt", 0x0, false);

    printf(",-----------------------------------------------------------------\n");
    printf("| [START]\n");


    do {
        token_p = QUEX_NAME(receive)(&qlex);

        /* print out token information */
        printf("%s \n", QUEX_NAME_TOKEN(get_string)(token_p));

        ++number_of_tokens;

        /* check against 'termination' */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", number_of_tokens);
    printf("`-----------------------------------------------------------------\n");

    QUEX_NAME(destruct)(&qlex);

    return 0;
}


