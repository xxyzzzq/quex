#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"


int 
main(int argc, char** argv) 
{        
    using namespace std;

    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple*       qlex = new quex::Simple(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;

    quex::Token   token;
    quex::Token*  token_p = &token;

#   ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
    qlex->token_p_set(&token);
#   endif

    // (*) loop until the 'termination' token arrives
    do {
#       ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
        (void)qlex->receive();
#       else
        token_p = qlex->receive();
#       endif
        cout << token_p->type_id_name() << endl;
        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    // cout << Token.type_id_name() << endl;
    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    cout << "buffer size = " << QUEX_SETTING_BUFFER_SIZE << endl;

    return 0;
}
