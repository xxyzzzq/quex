#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;
using namespace europa::deutschland::baden_wuertemberg;

int 
main(int argc, char** argv) 
{        
    // (*) create token
    ispringen::MeinToken      Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple     qlex(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    cout << "[START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        qlex.receive(&Token);
        cout << Token.type_id_name() << " ";

        switch( Token.type_id() ) {
        case QUEX_TKN_N1a: 
        case QUEX_TKN_N2a: 
        case QUEX_TKN_N3a: 
            cout << std::string((char*)Token.get_name().c_str()) << endl; 
            break;
        case QUEX_TKN_N1b: 
        case QUEX_TKN_N2b: 
        case QUEX_TKN_N3b: 
            cout << (int)Token.get_mini_x() << ", " << (int)Token.get_mini_y() << endl;
            break;
        case QUEX_TKN_N1c: 
        case QUEX_TKN_N2c: 
        case QUEX_TKN_N3c: 
            cout << (int)Token.get_big_x() << ", " << (int)Token.get_big_y() << endl;
            break;
        case QUEX_TKN_WHO: 
            cout << (int)Token.get_who_is_that() << endl; 
            break;
        }

        ++number_of_tokens;
        if( number_of_tokens > 100 ) {
            quex::QUEX_ERROR_EXIT("Loop beyond border.\n");
        }

    } while( Token.type_id() != QUEX_TKN_TERMINATION );

    cout << "\n[END] number of token = " << number_of_tokens << "\n";

    return 0;
}
