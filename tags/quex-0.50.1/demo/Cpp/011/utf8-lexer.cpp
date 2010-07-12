#include<cstdio> 

// (*) include lexical analyser header
#include "UTF8Lex"

using namespace std;

int 
main(int argc, char** argv) 
{        
    using namespace quex;

    Token*   token;
    UTF8Lex  qlex("example-utf8.txt");
    

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token = qlex.receive();

        // (*) print out token information
        printf("%s\n", (char*)(string(*token).c_str()));

        // (*) check against 'termination'
    } while( token->type_id() != TKN_TERMINATION );

    return 0;
}
