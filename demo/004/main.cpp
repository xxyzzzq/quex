#include<cstdio>    

#include "main.h"
#include <sys/stat.h>

static  FILE*           fh;
static  quex::c_lexer*  qlex; 
static  quex::Token     token; 

int 
main(int argc, char** argv) 
{        
    {
        if( argc != 2 ) { return -1; }

        fh = fopen(argv[1], "r");
        if( fh == NULL ) { 
            printf("File '%s' not found.\n", argv[1]);
            return -1;
        }
    }
#ifdef  ANALYZER_GENERATOR_FLEX
    yyin = fh; yyrestart(yyin);
#else
    qlex = new c_lexer(fh);
#   ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
    qlex->token = &token;
#   endif
#endif

#   if   defined(QUEX_QUICK_BENCHMARK_VERSION)
    const double  ExperimentTime = 1.0;   // [sec]
#   elif defined(QUEX_BENCHMARK_SERIOUS)
    const double  ExperimentTime = 10.0;  // [sec]
#   else
    const double  ExperimentTime = 0.0;   // [sec]
#   endif

    int           checksum = 0xFFFF;
    const size_t  TokenN   = count_token_n(func_get_token_id, &checksum); 
    const size_t  FileSize = get_file_size(argv[1]);
    double        repetition_n = -1;

    /* OVERHEAD MEASUREMENT */
    func_reset();
    const double  RefTime = benchmark(func_empty, func_reset,
                                      ExperimentTime / 20.0, 
                                      TokenN, 
                                      /* CheckSum */ -1, 
                                      &repetition_n);

    const clock_t RefTimePerRun = report("only overhead", RefTime, repetition_n, FileSize, /* CharacterSize = 1 */ 1);

    /* REAL MEASUREMENT */
    const double  Time = benchmark(func_get_token_id, func_reset,
                                   ExperimentTime, 
                                   TokenN, 
                                   checksum, 
                                   &repetition_n);
    const double  TimePerRun = report("analyzis + overhead", Time, repetition_n, FileSize, /* CharacterSize = 1 */ 1);
    
    final_report(TimePerRun, RefTimePerRun, argv[0], argv[1], FileSize, TokenN, repetition_n);
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
func_get_token_id()
{
#ifdef  ANALYZER_GENERATOR_FLEX
    return yylex();
#else
#   ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
    qlex->receive(); 
#   else
    qlex->receive(&token); 
#   endif
    return token.type_id();
#endif
}

QUEX_TYPE_TOKEN_ID 
func_empty()
{
    return (QUEX_TYPE_TOKEN_ID)1;
}

void
func_reset()
{
#ifdef  ANALYZER_GENERATOR_FLEX
    fseek(yyin, 0, SEEK_SET); 
    yyrestart(yyin);
#else
    qlex->reset(fh);
#endif
}
