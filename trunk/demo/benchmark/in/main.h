#ifndef __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__
#define __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__

#include "in/token-ids.h"

#include <cstdio>
#include <ctime>
#include <cstdlib>

using namespace std;

extern  FILE*  global_fh;

#if   defined(ANALYZER_GENERATOR_FLEX)
#    include <in/flex/adaption.h>
#elif defined(ANALYZER_GENERATOR_RE2C)
#    include <in/re2c/adaption.h>
#else
#    include <in/quex/adaption.h>
#endif

// in/*/adaption.c
void      scan_init(size_t FileSize);

// main.cpp
size_t             get_file_size(const char*, bool SilentF=false);
QUEX_TYPE_TOKEN_ID pseudo_scan();

// lexer.cpp
int       run_multiple_analyzis(size_t RepetitionN, size_t TokenN, bool PsuedoF);
void      get_statistics(int* checksum, int* token_n, double* time_per_run_ms);

// report.cpp:
void      print_date_string();
double    report(const char* Name, double Time, double RepetitionN, size_t FileSize, size_t CharacterSize);
void      final_report(double TimePerRun, double RefTimePerRun, 
                       const char* Filename, size_t FileSize, size_t TokenN, double RepetitionN,
                       size_t      ExecutableSize);

#endif /* __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__ */
