/* PURPOSE: Adaption of the benchmark suite to different lexical analysers.
 *          The analyser is to be defined by the macro:
 *          
 *          BENCHMARK_SETTING_ANALYSER
 *
 *          Possible values are: 'Quex', 'Flex'.
 *
 *          The idea is to make it very easy to include new lexical analyser generators
 *          into the benchmarking suite.
 *
 * (C) 2008 Frank-Rene Schaefer                                                           */
#ifndef __INCLUDE_GUARD__QUEX__C_LEXER__CONFIGURATION__
#define __INCLUDE_GUARD__QUEX__C_LEXER__CONFIGURATION__

#if ANALYZER_GENERATOR_FLEX

#   define BENCHMARK_SETTING_HEADER \
           extern int    yylex();
           extern FILE*  yyin;
           extern void   yyrestart(FILE*);
#else

#   define BENCHMARK_SETTING_HEADER \
           using namespace quex;

#endif

#endif /* __INCLUDE_GUARD__QUEX__C_LEXER__CONFIGURATION__ */

