#include<cstdio> 

// (*) include lexical analyser header
#include "ISO8859_7_Lex"
#include "ISO8859_7_Lex-converter-iso8859_7"

using namespace std;

int 
main(int argc, char** argv) 
{        
    using namespace quex;

    Token*           token;
    Token::__string  tmp;
    ISO8859_7_Lex    qlex("example-iso8859-7.txt");
    

    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token = qlex.receive();

        // (*) print out token information
        printf("%s\t", (char*)token->type_id_name().c_str());
        printf("%s\n",   (char*)Quex_iso8859_7_to_utf8_string(token->get_text()).c_str());
#       if 0
        cout << "\t\t plain bytes: ";
        for(QUEX_TYPE_CHARACTER* iterator = (uint8_t*)tmp.c_str(); *iterator ; ++iterator) {
            printf("%02X.", (int)*iterator);
        }
#       endif

        // (*) check against 'termination'
    } while( token->type_id() != TKN_TERMINATION );

    return 0;
}
