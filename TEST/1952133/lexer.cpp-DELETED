#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"


int 
main(int argc, char** argv) 
{        
    using namespace std;

    // (*) create token
    quex::Token*    token = 0x0;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple*   qlex = new quex::Simple(argc == 1 ? "example.txt" : argv[1]);

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

    std::printf("Buffer Size = %i\n", QUEX_SETTING_BUFFER_SIZE); 
    // cout << token->type_id_name() << endl;
    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    cout << "buffer size = " << QUEX_SETTING_BUFFER_SIZE << endl;

    delete qlex;
    return 0;
}
