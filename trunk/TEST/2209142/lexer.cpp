#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./Simple>

using namespace std;

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::Token        token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple  qlex("example.txt");

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    qlex.token_p_set(&token);
    do {
        // (*) get next token from the token stream
        (void)qlex.receive();

        // (*) print out token information
        //     -- line number and column number
        cout << "(" << qlex.line_number() << ", " << qlex.column_number() << ")  \t";
        //     -- name of the token
        cout << string(token);
        cout << endl;

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token.type_id() != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
