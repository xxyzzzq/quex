#include <stdio.h> 

// (*) include lexical analyser header
#include "UTF8Lex"
#include "UTF8Lex-token.i"

int 
main(int argc, char** argv) 
{        
    Token*   token_p = 0x0;
    size_t   BufferSize = 1024;
    char     buffer[1024];
    UTF8Lex  qlex;
    
    QUEX_NAME(construct_file_name)(&qlex, "example-utf8.txt", 0x0, false);

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token_p = QUEX_NAME(receive)(&qlex);

        /* (*) print out token information
         *     'get_string' automagically converts codec bytes into utf8 */
        printf("%s\n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));

        // (*) check against 'termination'
    } while( token_p->_id != TKN_TERMINATION );

    return 0;
}
