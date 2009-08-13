#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    quex::Token    token;
    quex::Simple   qlex(argv[1]);

    do {
        qlex.receive(&token);

        cout << token << endl;

    } while( token.type_id() != QUEX_TKN_TERMINATION );

    return 0;
}
