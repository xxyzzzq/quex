#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    quex::Token    Token;
    quex::Simple   qlex("example.txt");

    do {
        qlex.receive(&Token);
        if( Token.type_id() != QUEX_TKN_TERMINATION ) { cout << string(Token) << endl; } 
        else                                          { cout << Token.type_id_name() << endl; }
    } while( Token.type_id() != QUEX_TKN_TERMINATION );
    return 0;
}
