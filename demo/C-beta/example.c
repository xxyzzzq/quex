#include<stdio.h>    

#include "EasyLexer"
#include "EasyLexer-token.i"


#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

int 
main(int argc, char** argv) 
{        
    Token*       token_p = 0x0;
    size_t       number_of_tokens = 0;
    EasyLexer    qlex;
    const size_t UTF8ContentSize = 1024;
    uint8_t      utf8_content[1024];

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
#       ifdef PRINT_TOKEN
        uint8_t* end =
        QUEX_NAME(unicode_to_utf8_string)(token_p->text, 
                                          QUEX_NAME(strlen)(token_p->text),
                                          utf8_content,
                                          UTF8ContentSize);
        *end = '\0';
        printf("%s '%s'\n", 
               QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id),
               (const char*)utf8_content);
#       else
        printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
#       endif

#       ifdef SPECIAL_ACTION
        SPECIAL_ACTION(&qlex, &my_token);
#       endif
        ++number_of_tokens;

        /* Check against 'termination'            */
    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", number_of_tokens);
    printf("`------------------------------------------------------------------------------------\n");

    return 0;
}
