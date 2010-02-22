#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "EasyLexer"

#ifndef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
#   error "This example has been designed for token policy users_token."
#endif

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

int 
main(int argc, char** argv) 
{        
    using namespace std;

    quex::Token        my_token;
    // (*) create the lexical analyser
    //     1st arg: input file, default = 'example.txt'
    //     2nd arg: input character encoding name, 0x0 --> no codec conversion
    quex::EasyLexer    qlex(argc == 1 ? "example.txt" : argv[1], ENCODING_NAME);

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    qlex.token_p_set(&my_token);
    QUEX_TYPE_TOKEN_ID token_id = QUEX_TKN_UNINITIALIZED;
    do {
        // (*) get next token from the token stream
        token_id = qlex.receive();

        // (*) print out token information
#       ifdef PRINT_TOKEN
        cout << string(my_token) << endl;
#       else
        cout << my_token.type_id_name() << endl;
#       endif

#       ifdef SPECIAL_ACTION
        SPECIAL_ACTION(&qlex, &my_token);
#       endif

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token_id != QUEX_TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
