#ifndef __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__
#define __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__

#include "token-ids.h"
#if defined(ANALYZER_GENERATOR_FLEX)
#else
#    include "c_lexer"
#endif
#include <cstdio>
#include <ctime>
#include <cstdlib>

using namespace std;

/* NOTE: the following *must* be included after 'c_lexer' */
#if ANALYZER_GENERATOR_FLEX
   extern int    yylex();
   extern FILE*  yyin;
   extern void   yyrestart(FILE*);

   typedef int QUEX_TYPE_TOKEN_XXX_ID;
#else
   using namespace quex;
#endif

typedef QUEX_TYPE_TOKEN_XXX_ID   (*GetTokenIDFuncP)(void);
typedef void                 (*ResetFuncP)(void);

// main.cpp
QUEX_TYPE_TOKEN_XXX_ID func_get_token_id();
QUEX_TYPE_TOKEN_XXX_ID func_empty();
void               func_reset();

size_t    get_file_size(const char*, bool SilentF=false);

// lexer.cpp
double    benchmark(GetTokenIDFuncP, ResetFuncP, const double MinExperimentTime_sec,
                    size_t TokenN, int CheckSum, double* repetition_n);
size_t    count_token_n(GetTokenIDFuncP FuncP_get_token_id, int* checksum);

// report.cpp:
void      print_date_string();
double    report(const char* Name, double Time, double RepetitionN, size_t FileSize, size_t CharacterSize);
void      final_report(double TimePerRun, double RefTimePerRun, 
                       const char* Filename, size_t FileSize, size_t TokenN, double RepetitionN,
                       size_t      ExecutableSize);

#endif /* __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__ */
