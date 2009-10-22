#include<cstdio> 

// (*) include lexical analyser header
#include "UTF8Lex"

using namespace std;

int 
main(int argc, char** argv) 
{        
    using namespace quex;

    Token    token;
    UTF8Lex  qlex("example-utf8.txt");
    

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&token);

        // (*) print out token information
        printf("%s\t", (char*)token.type_id_name().c_str());
        printf("%s\n", (char*)(token.get_text()).c_str());

        // (*) check against 'termination'
    } while( token.type_id() != TKN_TERMINATION );

    return 0;
}
