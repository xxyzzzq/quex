#include<fstream>    
#include<iostream> 

#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // we want to have error outputs in stdout, so that the unit test could see it.
    quex::Token   Token;
    quex::Simple  qlex(argc == 1 ? "example.txt" : argv[1]);

    cout << "## An Assert-Abortion might be an intended element of the experiment.\n";
    do {
        qlex.get_token(&Token);
        cout << string(Token) << endl;
    } while( Token.type_id() != QUEX_TKN_TERMINATION );

    return 0;
}

