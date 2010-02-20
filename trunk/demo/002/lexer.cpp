#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include <./tiny_lexer>

using namespace std;

int 
main(int argc, char** argv) 
{        
    quex::Token*       token_p = 0x0;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer   qlex(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token_p = qlex.receive();

        // (*) print out token information
        //     -- name of the token
        cout << token_p->type_id_name() << endl;

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
