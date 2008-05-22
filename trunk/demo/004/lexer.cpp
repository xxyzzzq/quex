#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "tiny_lexer"
#include <ctime>
#include <cstdlib>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

using namespace std;

float  benchmark(std::FILE*, const size_t FileSize, float* repetition_n);

float  overhead(std::FILE*, 
                const int SimulatedFileSize, const size_t SimulatedTokenN, 
                const float RepetitionN);

size_t get_file_size(const char*);
size_t count_token_n(std::FILE*);
float  report(clock_t StartTime, float RepetitionN, size_t FileSize, size_t CharacterSize);

int 
main(int argc, char** argv) 
{        
    std::FILE*  fh = 0x0;

    if( argc != 2 ) { return -1; }

    fh = fopen(argv[1], "r");
    if( fh == NULL ) { 
        cerr << "File '" << argv[1] << "' not found.\n";
        return -1;
    }

    const size_t TokenN = count_token_n(fh); 
    fseek(fh, 0, SEEK_SET);
    const size_t FileSize = get_file_size(argv[1]);
    fseek(fh, 0, SEEK_SET);
    float        repetition_n;
    const float  TimePerRun_sec = benchmark(fh, FileSize, &repetition_n);
    fseek(fh, 0, SEEK_SET);
    /* Measure the overhead of the measurement */
    const float  RefTimePerRun_sec = overhead(fh, FileSize, TokenN, repetition_n);

    cout << (TimePerRun_sec - RefTimePerRun_sec) << endl;

    return 0;
} 

#ifndef QUEX_BENCHMARK_SERIOUS
void __PRINT_START()
{
        cout << ",------------------------------------------------------------------------------------\n";
        cout << "| [START]\n";
        int number_of_tokens = 0;
}
void __PRINT_END(int TokenN)
{
    cout << "| [END] number of token = " << number_of_tokens << "\n";
    cout << "`------------------------------------------------------------------------------------\n";
}
void __PRINT_TOKEN(const char* TokenName)
{
    cout << TokenP->type_id_name() << endl;
    ++(*number_of_tokens);
}
#else 
void __PRINT_START() { }
void __PRINT_END(int TokenN) { }
void __PRINT_TOKEN(const char* TokenName, int* number_of_tokens) { }
#endif

float
benchmark(std::FILE* fh, const size_t FileSize, float* repetition_n)
{
    using namespace std;
    quex::token*   TokenP;
    //
    // -- repeat the experiment, so that it takes at least 5 seconds
    const clock_t  MinExperimentTime = 10 * CLOCKS_PER_SEC;
    const clock_t  StartTime = clock();
    int            checksum = 0;
    int            checksum_ref = -1;
    //
    quex::tiny_lexer* qlex = new quex::tiny_lexer(fh);

    while( clock() < MinExperimentTime ) { 
        checksum       = 777;
        *repetition_n += 1.0f;
        __PRINT_START(); /* No Operation if QUEX_BENCHMARK_SERIOUS is defined */
        
        do {  
            qlex->get_token(&TokenP);

            checksum = (checksum + TokenP->type_id()) % 0xFF; 

            __PRINT_TOKEN(TokenP->type_id());  /* No Operation, see above */

        } while( TokenP->type_id() != quex::TKN_TERMINATION );

        __PRINT_END(number_of_tokens);
        if( checksum_ref == -1 ) { 
            checksum_ref = checksum; 
        }
        else if( checksum != checksum_ref ) {
            cerr << "run:                " << *repetition_n << endl;
            cerr << "checksum-reference: " << checksum_ref << endl;
            cerr << "checksum:           " << checksum     << endl;
            throw std::runtime_error("Checksum failure");
        }
        qlex->_reset();
    }
    
    return report(StartTime, *repetition_n, FileSize, /* CharacterSize = 1 */ 1);
}

float 
overhead(std::FILE* fh,
         const int SimulatedFileSize, const size_t SimulatedTokenN, const float RepetitionN)
{
    // This function is supposed to perform all 'frame' operations, but not the
    // analyzer function. This is to estimate the overhead implied by the test program.
    const clock_t StartTime = clock();
    float         repetition_n = 0.0;
    int           checksum = 0;
    const size_t  end = SimulatedTokenN * RepetitionN;
    //
    quex::tiny_lexer* qlex = new quex::tiny_lexer(fh);

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
    // The 'Checksum' is printed for the sole purpose to prevent that the 
    // checksum computation is not optimized away. When the checksum computation is not
    // optimized away, then the token id reception cannot be optimized away.
    std::cout << "Checksum (meaningless): " << checksum << " [1]" << std::endl;
    return report(StartTime, RepetitionN, SimulatedFileSize, /* CharacterSize [byte] */ 1);
}

float
report(clock_t StartTime, float RepetitionN, size_t FileSize, size_t CharacterSize)
{ 
    using namespace std;

    const float   CPU_Freq      = 1866.781e6;
    const float   CycleTime_sec = 1.0 / CPU_Freq;
    const clock_t EndTime    = clock();
    const float   TimeDiff   = (float)(EndTime - StartTime) / (float)CLOCKS_PER_SEC;
    const float   TimePerRun = TimeDiff / RepetitionN;
    const float   TimePerChar= TimePerRun / (float(FileSize) / float(CharacterSize));
    const float   CCC        = TimePerChar / CycleTime_sec;

    cout << "Total Time:  " << TimeDiff          << " [sec]" << endl;
    cout << "Runs:        " << (long)RepetitionN << " [1]"   << endl;
    cout << "TimePerRun:  " << TimePerRun        << " [sec]" << endl;
    cout << "TimePerChar: " << TimePerChar       << " [sec]" << endl;
    cout << "Clocks/Char: " << CCC               << " [clock cycles]" << endl;

    return TimePerRun;
}

size_t
count_token_n(std::FILE* fh)
{
    using namespace std;
    quex::tiny_lexer*  qlex = new quex::tiny_lexer(fh);
    quex::token*       TokenP;
    int token_n = 0;

    // (*) loop until the 'termination' token arrives
    for(token_n=0; ; ++token_n) {
        qlex->get_token(&TokenP);
        if( TokenP->type_id() == quex::TKN_TERMINATION ) break;
    } 
    cout << "TokenN: " << token_n << " [1]"   << endl;
    return token_n;
}

size_t
get_file_size(const char* Filename)
{
    using namespace std;
    struct stat s;
    stat(Filename, &s);
    cout << "FileSize: " << s.st_size << " [1]"   << endl;
    return s.st_size;
}
