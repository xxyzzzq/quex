#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "tiny_lexer"
#include <ctime>


int 
main(int argc, char** argv) 
{        
    using namespace std;
    clock_t  start_time = (clock_t)0;
    clock_t  end_time   = (clock_t)0;

    // (*) create token
    quex::token        Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer*  qlex = new quex::tiny_lexer(argc == 1 ? "example.txt" : argv[1]);

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

#ifndef QUEX_BENCHMARK_SERIOUS
    cout << ",------------------------------------------------------------------------------------\n";
    cout << "| [START]\n";
    int number_of_tokens = 0;
#endif

    // (*) loop until the 'termination' token arrives
    start_time = clock();
    do {
        // (*) get next token from the token stream
        qlex->get_token(&Token);

        // (*) print out token information
        //     -- name of the token
#ifndef QUEX_BENCHMARK_SERIOUS
        cout << Token.type_id_name() << endl;

        ++number_of_tokens;
#endif

        // (*) check against 'termination'
    } while( Token.type_id() != quex::TKN_TERMINATION );
    end_time = clock();
    cout << (end_time - start_time) << endl;
    cout << float(end_time - start_time) / (float)CLOCKS_PER_SEC << endl;

    // cout << Token.type_id_name() << endl;
#ifndef QUEX_BENCHMARK_SERIOUS
    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";
#endif

    return 0;
}
