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

#if __BENCHMARK_SETTING_ANALYSER == "Quex"

#   define BENCHMARK_SETTING_HEADER \
           #include <c_lexer>

#   define BENCHMARK_SETTING_INIT           quex::c_lexer   qlex(fh);
#   define BENCHMARK_SETTING_GET_TOKEN_ID   token_id = qlex.get_token();
#   define BENCHMARK_SETTING_RESET          qlex._reset();

#elif __BENCHMARK_SETTING_ANALYSER == "Flex"

#   define BENCHMARK_SETTING_HEADER \
           int yylex();

#   define BENCHMARK_SETTING_INIT           yyin = fh; yyrestart(yyin);
#   define BENCHMARK_SETTING_GET_TOKEN_ID   (token_id = yylex())
#   define BENCHMARK_SETTING_RESET          fseek(yyin, 0, SEEK_SET); yyrestart(yyin);

#else

#   error "Benchmark type '" __BENCHMARK_SETTING_ANALYSER "' is not supported."

#endif

#endif /* __INCLUDE_GUARD__QUEX__C_LEXER__CONFIGURATION__ */

