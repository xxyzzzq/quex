#ifndef __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__
#define __INCLUDE_GUARD__QUEX__BENCHMARK_MAIN_H__

#include "token-ids.h"
#if    defined(ANALYZER_GENERATOR_FLEX) \
    || defined(ANALYZER_GENERATOR_RE2C)
#else
#    include "c_lexer"
#endif
#include <cstdio>
#include <ctime>
#include <cstdlib>

using namespace std;

extern  FILE*  global_fh;

/* NOTE: the following *must* be included after 'c_lexer' */
#if ANALYZER_GENERATOR_FLEX
   extern int    yylex();
   extern FILE*  yyin;
   extern void   yyrestart(FILE*);

   typedef int QUEX_TYPE_TOKEN_ID;
#  define ANALYZER_ANALYZE(TokenID) \
          do {                      \
              TokenID = yylex();    \
          } while ( 0 )

#  define ANALYZER_RESET() \
          do {                          \
             fseek(yyin, 0, SEEK_SET);  \
             yyrestart(yyin);           \
          } while( 0 )

#elif defined(ANALYZER_GENERATOR_RE2C)
   extern char*  global_re2c_buffer_begin;
   extern char*  global_re2c_buffer_end;
   extern char*  global_re2c_buffer_iterator;

#  define QUEX_TYPE_TOKEN_ID  int
   QUEX_TYPE_TOKEN_ID re2c_scan(char** p);
#  define ANALYZER_ANALYZE(TokenID) \
          do {                                                   \
              TokenID = re2c_scan(&global_re2c_buffer_iterator); \
          } while ( 0 )

#  define ANALYZER_RESET() \
          do {                                                        \
              global_re2c_buffer_iterator = global_re2c_buffer_begin; \
          } while ( 0 )

#else
    extern quex::c_lexer*  global_qlex; 
    extern quex::Token     global_token; 
    using namespace quex;
#  ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
#     define ANALYZER_ANALYZE(TokenID)       \
              do {                           \
                  global_qlex->receive();           \
                  TokenID = global_token.type_id(); \
              } while( 0 )
#  else
#     define ANALYZER_ANALYZE(TokenID)       \
              do {                           \
                  global_qlex->receive(&global_token); \
                  TokenID = global_token.type_id();    \
              } while( 0 )
#  endif
#  define ANALYZER_RESET() \
              do {                          \
                  fseek(global_fh, 100, SEEK_SET); \
                  global_qlex->reset(global_fh);   \
              } while( 0 )

#endif
#define ANALYZER_PSEUDO_ANALYZE(TokenID) TokenID = func_empty()

typedef QUEX_TYPE_TOKEN_ID   (*GetTokenIDFuncP)(void);
typedef void                 (*ResetFuncP)(void);

// main.cpp
QUEX_TYPE_TOKEN_ID func_get_token_id();
QUEX_TYPE_TOKEN_ID func_empty();
void               func_reset();

size_t    get_file_size(const char*, bool SilentF=false);

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
