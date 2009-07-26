#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;

    int 
main(int argc, char** argv) 
{        
    // (*) create token
    quex::Token        token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
#   if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
    quex::Simple  qlex(argv[1], "UTF-8");
#   else
    quex::Simple  qlex(argv[1]);
#   endif


    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        // (*) get next token from the token stream
        qlex.receive(&token);

        // (*) print out token information
        //     -- name of the token
        if( token.type_id() != TKN_TERMINATION ) { 
#           if defined (QUEX_OPTION_ENABLE_ICU) || defined (QUEX_OPTION_ENABLE_ICONV)
            cout << token << endl;
#           else
            cout << (const char*)(token.type_id_name().c_str()) << " '" << (const char*)(token.text().c_str()) << "' " << endl;
#           endif
        } 
        else { 
            cout << token.type_id_name() << endl;
        }

        ++number_of_tokens;

        // (*) check against 'termination'
    } while( token.type_id() != TKN_TERMINATION );

    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}
