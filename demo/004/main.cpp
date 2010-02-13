#include<cstdio>    

#include "main.h"
#include <sys/stat.h>

FILE*   global_fh;
#if  defined(ANALYZER_GENERATOR_FLEX) || defined(ANALYZER_GENERATOR_RE2C)
#else
quex::c_lexer*  global_qlex; 
quex::Token     global_token; 
#endif

int 
main(int argc, char** argv) 
{        
    {
        if( argc != 2 ) { return -1; }

        global_fh = fopen(argv[1], "r");
        if( global_fh == NULL ) { 
            printf("File '%s' not found.\n", argv[1]);
            return -1;
        }
    }
    const size_t   FileSize = get_file_size(argv[1]);

#if   defined(ANALYZER_GENERATOR_FLEX)
    yyin = global_fh; yyrestart(yyin);
#elif defined(ANALYZER_GENERATOR_RE2C)
    global_re2c_buffer_begin    = (char*)malloc(sizeof(char)*(size_t)(FileSize * 2));
    global_re2c_buffer_iterator = global_re2c_buffer_begin;
    /* re2c does not provide the slightest buffer management, 
     * => load the whole bunch at once.                        */
    size_t Size = fread(global_re2c_buffer_begin, 1, (size_t)(FileSize * 2), global_fh);
    /* Set the terminating zero */
    *(global_re2c_buffer_begin + Size + 1) = '\0';
    global_re2c_buffer_end = global_re2c_buffer_begin + FileSize;
#else
    global_qlex = new c_lexer(global_fh);
#   ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
    global_qlex->token = &global_token;
#   endif
#endif

#   if   defined(QUEX_QUICK_BENCHMARK_VERSION)
    const double   ExperimentTime = 1.0;   // [sec]
#   elif defined(QUEX_BENCHMARK_SERIOUS)
    const double   ExperimentTime = 10.0;  // [sec]
#   else
    const double   ExperimentTime = 0.0;   // [sec]
#   endif

    int     checksum        = 0xFFFF;
    int     token_n         = (size_t)-1;
    double  time_per_run_ms = -1.0;
    {
        get_statistics(&checksum, &token_n, &time_per_run_ms);
    }
    const size_t   RepetitionN = ExperimentTime / time_per_run_ms;

    /* Measure the analyzis time + some overhead ______________________________*/
    const clock_t  StartTime = clock();
    {
        run_multiple_analyzis(RepetitionN, token_n, /* PseudoF */false);
    }
    const clock_t  EndTime = clock();
    const double   Time_ms = (double)(EndTime - StartTime) / (double)CLOCKS_PER_SEC; 
    const double   TimePerRun_ms = Time_ms / (double)RepetitionN;

    /* Measure the overhead ___________________________________________________*/
    const clock_t  RefStartTime = clock();
    {
        run_multiple_analyzis(RepetitionN, token_n, /* PseudoF */true);
    }
    const clock_t  RefEndTime = clock();
    const double   RefTime_ms = (double)(RefEndTime - RefStartTime) / (double)CLOCKS_PER_SEC; 
    const double   RefTimePerRun_ms = RefTime_ms / (double)RepetitionN;

    /* Raw analyzis time = ... */
    /* const double   RawTime_ms = Time_ms - RefTime_ms; */

    /* Reporting _____________________________________________________________*/
    report("only overhead",       RefTime_ms, RepetitionN, FileSize, /* CharacterSize = 1 */ 1);
    report("analyzis + overhead", Time_ms, RepetitionN, FileSize, /* CharacterSize = 1 */ 1);
    
    final_report(TimePerRun_ms, RefTimePerRun_ms, 
                 argv[1], FileSize, 
                 token_n, RepetitionN, 
                 get_file_size(argv[0], true));
    return 0;
} 

size_t
get_file_size(const char* Filename, bool SilentF /*=false*/)
{
    using namespace std;
    struct stat s;
    stat(Filename, &s);
    if( ! SilentF ) {
        printf("// FileSize: %i [Byte] = %f [kB] = %f [MB].\n", 
               (int)s.st_size,
               (float)(double(s.st_size) / double(1024.0)),
               (float)(double(s.st_size) / double(1024.0*1024.0)));
    }
    return s.st_size;
}

QUEX_TYPE_TOKEN_ID 
func_empty()
{
    return (QUEX_TYPE_TOKEN_ID)1;
}

