#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "IndigoLexer"

using namespace std;

int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::Token*         token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::IndigoLexer*   qlex = new quex::IndigoLexer(argc == 1 ? "example.dat" : argv[1], "UTF-32LE");

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        token = qlex->receive();

        // (*) print out token information
        //     -- name of the token
        cout << token->type_id_name() << endl;

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token->type_id() != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
