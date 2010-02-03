#include "main.h"

#define CHECKSUM_INIT_VALUE               (0x77)
#define CHECKSUM_ACCUMULATE(CS, TokenID)  (((CS) + (TokenID)) % 0xFF)

#ifndef QUEX_BENCHMARK_SERIOUS
void __PRINT_END()
{ printf("`------------------------------------------------------------------------------------\n"); }
#else 
#   define __PRINT_END() /* empty */
#endif

double
benchmark(GetTokenIDFuncP FuncP_get_token_id, ResetFuncP FuncP_reset, 
          const double MinExperimentTime_sec,
          size_t TokenN, int CheckSum, double* repetition_n)
{
    register int   token_id     = TKN_TERMINATION;
    const clock_t  StartTime    = clock();
    const clock_t  MinExperimentTime = (clock_t)(MinExperimentTime_sec * (double)CLOCKS_PER_SEC);
    const clock_t  EndTime           = StartTime + MinExperimentTime;
    clock_t        current_time = 0;
    int            checksum     = 0;
    
    FuncP_reset();

    do { 
        checksum       = CHECKSUM_INIT_VALUE;
        *repetition_n += 1.0f;
        
        for(size_t token_i = 0; token_i < TokenN; ++token_i) {
            token_id = FuncP_get_token_id();

            // checksum = (checksum + TokenP->type_id()) % 0xFF; 
            checksum = CHECKSUM_ACCUMULATE(checksum, token_id); 
#           if ! defined(QUEX_BENCHMARK_SERIOUS)
            printf("TokenID = %s\n", (const char*)(quex::Token::map_id_to_name(token_id)));
            printf("(%i) Checksum: %i\n", (int)token_i, (int)checksum);
#           endif
        } 
        // Overhead-Intern: (addition, modulo division, assignment, increment by one, comparison) * token_n

        __PRINT_END();
        /* During 'real' testing the checksum == CheckSum, this the second block is entered.
         * There another trivial test is done, thus:
         * (1) 'real' tests --> 2x trivial tests.
         *
         * During 'overhead' testing the checksum != CheckSum and the first block is entered.
         * Again, a trivial tests to prevent eroneous error reports, thus:
         * (2) 'overhead' tests --> 2x trivial tests.                                          
         *
         * In both cases the same number of trivial tests.                                     */
        if( checksum != CheckSum ) {
            if( CheckSum  != -1 ) {
                fprintf(stderr, "run:                %i\n", (int)*repetition_n);
                fprintf(stderr, "checksum-reference: %i\n", (int)CheckSum);
                fprintf(stderr, "checksum:           %i\n", (int)checksum);
                exit(-1);
            }
        } else {
            if( CheckSum == -1 ) {
                printf("#################\n");
                printf("## Weird World ##\n");
                printf("#################\n");
                exit(-1);
            }
        }
        FuncP_reset();

        current_time = clock();
    } while( current_time < EndTime );
    
    /* Make sure, that the 'clock()' function call is not optimized strangely. */
    current_time = clock();
    return (double)(current_time - StartTime) / double(CLOCKS_PER_SEC);
}

size_t
count_token_n(GetTokenIDFuncP FuncP_get_token_id, int* checksum)
{
    int token_id = TKN_TERMINATION;
    int token_n  = 0;
    *checksum    = CHECKSUM_INIT_VALUE;

    // (*) loop until the 'termination' token arrives
    for(token_n=0; ; ++token_n) {
        token_id  = FuncP_get_token_id();
        *checksum = CHECKSUM_ACCUMULATE(*checksum, token_id); 
#       if ! defined(QUEX_BENCHMARK_SERIOUS)
        printf("TokenID = %s\n", (const char*)(quex::Token::map_id_to_name(token_id)));
        printf("(%i) Checksum: %i\n", (int)token_n, (int)*checksum);
#       endif
        if( token_id == TKN_TERMINATION ) break;
    } 
    printf("// TokenN: %i [1]\n", token_n);
    return token_n;
}

