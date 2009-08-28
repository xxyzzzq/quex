#ifndef __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__
#define __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__

#include "token-ids.h"
#if defined(ANALYZER_GENERATOR_FLEX)
#else
#    include "c_lexer"
#endif

/* NOTE: the following *must* be included after 'c_lexer' */
#if ANALYZER_GENERATOR_FLEX
   extern int    yylex();
   extern FILE*  yyin;
   extern void   yyrestart(FILE*);
#else
   using namespace quex;
#endif

using namespace std;

typedef QUEX_TYPE_TOKEN_ID   (*GetTokenIDFuncP)(void);
typedef void                 (*ResetFuncP)(void);

// main.cpp
QUEX_TYPE_TOKEN_ID func_get_token_id();
QUEX_TYPE_TOKEN_ID func_empty();
void               func_reset();

size_t    get_file_size(const char*, bool SilentF=false);

// lexer.cpp
double    benchmark(GetTokenIDFuncP, ResetFuncP, const clock_t MinExperimentTime,
                    size_t TokenN, int CheckSum, double* repetition_n);
size_t    count_token_n(GetTokenIDFuncP FuncP_get_token_id, int* checksum);

// report.cpp:
void      print_date_string();
double    report(const char* Name, clock_t Time, double RepetitionN, size_t FileSize, size_t CharacterSize);
void      final_report(double TimePerRun, double RefTimePerRun, const char* ThisExecutableName, 
                       const char* Filename, size_t FileSize, size_t TokenN, double RepetitionN);

#endif /* __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__ */
