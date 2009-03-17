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

#   define BENCHMARK_SETTING_INIT           yyin = fh; yyrestart(yyin);
#   define BENCHMARK_SETTING_GET_TOKEN_ID   token_id = yylex();
#   define BENCHMARK_SETTING_RESET          fseek(yyin, 0, SEEK_SET); yyrestart(yyin);

#   define BENCHMARK_SETTING_TERMINATE      /* */

#else

#   define BENCHMARK_SETTING_HEADER \
           using namespace quex;

#   define BENCHMARK_SETTING_INIT           quex::c_lexer   qlex(fh); quex::Token token; qlex.token = &token;
#   define BENCHMARK_SETTING_GET_TOKEN_ID   qlex.receive(); token_id = qlex.token->type_id();
#   define BENCHMARK_SETTING_RESET          qlex._reset();

#   define BENCHMARK_SETTING_TERMINATE      qlex.token = 0x0;


#endif

#endif /* __INCLUDE_GUARD__QUEX__C_LEXER__CONFIGURATION__ */

