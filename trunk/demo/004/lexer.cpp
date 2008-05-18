#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "tiny_lexer"
#include <ctime>
#include <cstdlib>


int 
main(int argc, char** argv) 
{        
    using namespace std;
    const clock_t  MinExperimentTime = 5 * CLOCKS_PER_SEC;
    clock_t        start_time = (clock_t)0;
    int            checksum = 0;
    int            checksum_ref = -1;

    // (*) create token
    quex::token        Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer*  qlex = new quex::tiny_lexer(argc == 1 ? "example.txt" : argv[1]);
    // -- repeat the experiment, so that it takes at least 5 seconds

    // (*) print the version 
    // cout << qlex->version() << endl << endl;

    // (*) loop until the 'termination' token arrives
    start_time = clock();
    float repetition_n = 0.0;
    while( clock() < MinExperimentTime ) { 
        repetition_n += 1.0f;
#       ifndef QUEX_BENCHMARK_SERIOUS
        cout << ",------------------------------------------------------------------------------------\n";
        cout << "| [START]\n";
        int number_of_tokens = 0;
#       endif
        
        do {
            // (*) get next token from the token stream
            qlex->get_token(&Token);

            checksum = (checksum + Token.type_id()) % 0x1000000; 

            // (*) print out token information
            //     -- name of the token
#           ifndef QUEX_BENCHMARK_SERIOUS
            cout << Token.type_id_name() << endl;
            ++number_of_tokens;
#           endif
            // (*) check against 'termination'
        } while( Token.type_id() != quex::TKN_TERMINATION );

#       ifndef QUEX_BENCHMARK_SERIOUS
        cout << "| [END] number of token = " << number_of_tokens << "\n";
        cout << "`------------------------------------------------------------------------------------\n";
#       endif
        if( checksum_ref == -1 ) { 
            checksum_ref = checksum; 
        }
        else if( checksum != checksum_ref ) {
            cerr << "run:                " << repetition_n << endl;
            cerr << "checksum-reference: " << checksum_ref << endl;
            cerr << "checksum:           " << checksum     << endl;
            throw std::runtime_error("Checksum failure");
        }
        checksum = 0;
        qlex->_reset();
    }
    { 
        const clock_t EndTime    = clock();
        const float   TimeDiff   = (float)(EndTime - start_time) / (float)CLOCKS_PER_SEC;
        const float   TimePerRun = TimeDiff / repetition_n;

        cout << "Total Time: " << TimeDiff << " [sec]" << endl;
        cout << "Runs:       " << (long)repetition_n << " [1]" << endl;
        cout << "TimePerRun: " << TimePerRun << " [sec]" << endl;
    }

    // cout << Token.type_id_name() << endl;

    return 0;
}
