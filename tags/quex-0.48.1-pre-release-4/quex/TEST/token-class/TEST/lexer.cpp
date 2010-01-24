#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"

using namespace std;
using namespace europa::deutschland::baden_wuertemberg;

int 
main(int argc, char** argv) 
{        
    if( argc > 1 && strcmp("--hwut-info", argv[1]) == 0 ) {
#   if   defined(TEST_simple)
        printf("With token policy 'users_token'.\n");
#   elif defined(TEST_simple_queue)
        printf("With token policy 'queue'.\n");
#   else
        printf("ERROR - unreviewed compilation - ERROR.\n");
#   endif
        return 0;
    }
    // (*) create token
    // ispringen::MeinToken*      token = new ispringen::MeinToken();
    ispringen::MeinToken      token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::Simple     qlex(argc == 1 ? "example.txt" : argv[1]);


    // (*) Access the '__nonsense__' member to ensure it has been generated
    token.__nonsense__ = 0;

    cout << "[START]\n";

    int number_of_tokens = 0;
    // (*) loop until the 'termination' token arrives
    do {
        qlex.receive(&token);
        cout << token.type_id_name() << " ";

        switch( token.type_id() ) {
        case QUEX_TKN_N1a: 
        case QUEX_TKN_N2a: 
        case QUEX_TKN_N3a: 
            cout << std::string((char*)token.get_name().c_str()) << endl; 
            break;
        case QUEX_TKN_N1b: 
        case QUEX_TKN_N2b: 
        case QUEX_TKN_N3b: 
            cout << (int)token.get_mini_x() << ", " << (int)token.get_mini_y() << endl;
            break;
        case QUEX_TKN_N1c: 
        case QUEX_TKN_N2c: 
        case QUEX_TKN_N3c: 
            cout << (int)token.get_big_x() << ", " << (int)token.get_big_y() << endl;
            break;
        case QUEX_TKN_WHO: 
            cout << (int)token.get_who_is_that() << endl; 
            break;
        }

        ++number_of_tokens;
        if( number_of_tokens > 100 ) {
            QUEX_ERROR_EXIT("Loop beyond border.\n");
        }

    } while( token.type_id() != QUEX_TKN_TERMINATION );

    cout << "\n[END] number of token = " << number_of_tokens << "\n";

    return 0;
}
