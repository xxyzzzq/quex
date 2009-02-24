#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"


int 
main(int argc, char** argv) 
{        
    using namespace std;

    // (*) create token
    quex::Token        Token;
    QUEX_TYPE_TOKEN_ID token_id = __QUEX_TOKEN_ID_UNINITIALIZED;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple*  qlex = new quex::Simple(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
#       ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE
        qlex->get_token(&Token);
        cout << Token.type_id_name() << endl;
        token_id = Token.type_id();
#       else
        token_id = qlex->get_token();
        cout << Token.map_id_to_name(token_id) << endl;
#       endif
        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token_id != __QUEX_TOKEN_ID_TERMINATION );

    // cout << Token.type_id_name() << endl;
    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    cout << "buffer size = " << QUEX_SETTING_BUFFER_SIZE << endl;

    return 0;
}
