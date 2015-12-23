#include <stdio.h>    

#include "EasyLexer.h"

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

static void print_token(quex_Token* token_p);

int 
main(int argc, char** argv) 
{        
    quex_Token*     token_p = NULL;
    size_t          number_of_tokens = 0;
    quex_EasyLexer  qlex;
    const char*     FileName = (argc == 1) ? "example.txt" : argv[1];

    quex_EasyLexer_from_file_name(&qlex, FileName, ENCODING_NAME);

    printf(",-----------------------------------------------------------------\n");
    printf("| [START]\n");

    do {
        quex_EasyLexer_receive(&qlex, &token_p);

        print_token(token_p);

        ++number_of_tokens;

    } while( token_p->_id != QUEX_TKN_TERMINATION );

    printf("| [END] number of token = %i\n", number_of_tokens);
    printf("`-----------------------------------------------------------------\n");

    quex_EasyLexer_destruct(&qlex);

    return 0;
}

static void
print_token(quex_Token* token_p)
{
#   ifdef PRINT_TOKEN
    const size_t    BufferSize = 1024;
    char            buffer[1024];
#   endif

#   ifdef PRINT_LINE_COLUMN_NUMBER
    printf("(%i, %i)  \t", (int)token_p->_line_n, (int)token_p->_column_n);
#   endif

#   ifdef PRINT_TOKEN
    switch( token_p->_id ) {
    case QUEX_TKN_INDENT: 
    case QUEX_TKN_DEDENT: 
    case QUEX_TKN_NODENT: 
    case QUEX_TKN_TERMINATION: 
        /* In this case, the token still carries an old lexeme; Printing it
         * would be confusing.                                               */
        printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
        break;
    default:
        printf("%s \n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));
        break;
    }
#   else
    printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
#   endif
}
