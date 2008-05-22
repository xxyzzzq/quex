#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "tiny_lexer"
#include <ctime>
#include <cstdlib>

void
benchmark(quex::tiny_lexer* qlex, const size_t FileSize);

void 
reference(quex::tiny_lexer* qlex, 
          const int SimulatedFileSize_kB, const size_t SimulatedTokenN, 
          const float RepetitionN);

void
count_token_n(quex::tiny_lexer* qlex);

void
report(const clock_t StartTime, const float RepetitionN, 
       const size_t FileSize_kB, const size_t CharacterSize);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    if( argc < 2 || argc == 4 || argc > 5 ) {
        cout << "Please, read the README.txt file!\n";
        return 0;
    }
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer*  qlex     = new quex::tiny_lexer(argv[1]);

    cout << argv[1];
    if( argc == 2 ) {
        cout << endl;
        count_token_n(qlex);
    }
    else if( argc == 3 ) { 
        // (*) The Benchmark Procedure
        cout << " " << argv[2] << endl;
        const size_t FileSize = atoi(argv[2]);
        benchmark(qlex, FileSize);
    }
    else if( argc == 5 ) { 
        // (*) Measure the Environment
        cout << " " << argv[2] << " " << argv[3] << endl;
        const size_t SimulatedFileSize_kB  = atof(argv[2]);
        const int    SimulatedTokenNPerRun = atof(argv[3]);
        const float  RepetitionN           = atoi(argv[4]);
        reference(qlex, SimulatedFileSize_kB, SimulatedTokenNPerRun, RepetitionN);
    } 

    return 0;
} 

void
benchmark(quex::tiny_lexer* qlex, const size_t FileSize_kB)
{
    using namespace std;
    quex::token*   TokenP;
    //
    // -- repeat the experiment, so that it takes at least 5 seconds
    const clock_t  MinExperimentTime = 10 * CLOCKS_PER_SEC;
    const clock_t  StartTime = clock();
    int            checksum = 0;
    int            checksum_ref = -1;
    float          repetition_n = 0.0;

    while( clock() < MinExperimentTime ) { 
        checksum      = 0;
        repetition_n += 1.0f;
#       ifndef QUEX_BENCHMARK_SERIOUS
        cout << ",------------------------------------------------------------------------------------\n";
        cout << "| [START]\n";
        int number_of_tokens = 0;
#       endif
        
        // (*) loop until the 'termination' token arrives
        do {
            // (*) get next token from the token stream
            qlex->get_token(&TokenP);

            checksum = checksum + TokenP->type_id(); 

            // (*) print out token information
            //     -- name of the token
#           ifndef QUEX_BENCHMARK_SERIOUS
            cout << TokenP->type_id_name() << endl;
            ++number_of_tokens;
#           endif
            // (*) check against 'termination'
        } while( TokenP->type_id() != quex::TKN_TERMINATION );

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
        qlex->_reset();
    }
    report(StartTime, repetition_n, FileSize_kB, /* CharacterSize = 1 */ 1);
}

void 
reference(quex::tiny_lexer* qlex, 
          const int SimulatedFileSize_kB, const size_t SimulatedTokenN, const float RepetitionN)
{
    // This function is supposed to perform all 'frame' operations, but not the
    // analyzer function. This is to estimate the overhead implied by the test program.
    const clock_t StartTime = clock();
    float         repetition_n = 0.0;
    int           checksum = 0;
    const size_t  end = SimulatedTokenN * RepetitionN;

    checksum = 0; // here: prevent optimizing away of token_n --> out of loop
    while( repetition_n < RepetitionN ) { 
        repetition_n += 1.0f;
        
        size_t token_n = 0;
        do {
            token_n = token_n + RepetitionN;  // use argument RepetitionN instead of a 
            //                              // constant, so that it cannot be optimized away.
        } while( token_n != end );
        // clock() needs to be called also 'repetition_n' times. 
        checksum += token_n ^ clock();

        qlex->_reset();
    }
    report(StartTime, RepetitionN, SimulatedFileSize_kB, /* CharacterSize [byte] */ 1);

    // The 'Checksum' is printed for the sole purpose to prevent that the 
    // checksum computation is not optimized away. When the checksum computation is not
    // optimized away, then the token id reception cannot be optimized away.
    std::cout << "Checksum (meaningless): " << checksum << " [1]" << std::endl;
}

void
report(const clock_t StartTime, const float RepetitionN, 
       const size_t FileSize_kB, const size_t CharacterSize)
{ 
    using namespace std;

    const float   CPU_Freq      = 1866.781e6;
    const float   CycleTime_sec = 1.0 / CPU_Freq;
    const clock_t EndTime    = clock();
    const float   TimeDiff   = (float)(EndTime - StartTime) / (float)CLOCKS_PER_SEC;
    const float   TimePerRun = TimeDiff / RepetitionN;
    const float   TimePerChar= TimePerRun / (float(FileSize_kB) * 1024.0 / CharacterSize);
    const float   CCC        = TimePerChar / CycleTime_sec;

    cout << "Total Time:  " << TimeDiff          << " [sec]" << endl;
    cout << "Runs:        " << (long)RepetitionN << " [1]"   << endl;
    cout << "TimePerRun:  " << TimePerRun        << " [sec]" << endl;
    cout << "TimePerChar: " << TimePerChar       << " [sec]" << endl;
    cout << "Clocks/Char: " << CCC               << " [clock cycles]" << endl;
}

void
count_token_n(quex::tiny_lexer* qlex)
{
    using namespace std;
    quex::token*   TokenP;
    int token_n = 0;

    // (*) loop until the 'termination' token arrives
    for(token_n=0; ; ++token_n) {
        qlex->get_token(&TokenP);
        if( TokenP->type_id() == quex::TKN_TERMINATION ) break;
    } 
    cout << "TokenN: " << token_n << " [1]"   << endl;
}
