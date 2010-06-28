#include <stdio.h> 

// (*) include lexical analyser header
#include "UTF8Lex"
#include "UTF8Lex-token.i"

int 
main(int argc, char** argv) 
{        
    Token*   token;
    UTF8Lex  qlex;
    
    QUEX_NAME(construct_file_name)(&qlex, "example-utf8.txt", 0x0, false);

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token = QUEX_NAME(receive)(&qlex);

        // (*) print out token information
        printf("%s\t", (char*)token->type_id_name().c_str());
        printf("%s\n", (char*)(token->get_text()).c_str());

        // (*) check against 'termination'
    } while( token->_id != TKN_TERMINATION );

    return 0;
}
