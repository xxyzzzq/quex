#include "main.h"

#define CHECKSUM_INIT_VALUE               (0x77)
#define CHECKSUM_ACCUMULATE(CS, TokenID)  (((CS) + (TokenID)) % 0xFF)

#ifndef QUEX_BENCHMARK_SERIOUS
void __PRINT_END()
{ printf("`------------------------------------------------------------------------------------\n"); }
#else 
#   define __PRINT_END() /* empty */
#endif

int
run_multiple_analyzis(size_t RepetitionN, size_t TokenN, bool PseudoF)
    /* PseudoF == true: Execute only the 'overhead' not the real
     *                  analyzsis.                                */
{
    register int token_id  = TKN_TERMINATION;
    int          checksum  = 0;
    size_t       token_i   = (size_t)-1; 
    size_t       i         = 0;

    ANALYZER_RESET();
    /* The only reason of the checksum is to prevent that the return value
     * of the analyzis is not ommitted by the compiler, because it is not used.
     * Maybe, in this case, even the function call might be omitted.            */
    checksum = CHECKSUM_INIT_VALUE;

    for(i = 0; i < RepetitionN; ++i) {

        /* Assume that the time spent in ANALYZER_ANALYZE/ANALYZER_PSEUDO_ANALYZE
         * is much higher than the test for 'PseudoF' so it will to influence the
         * measurement.                                                           */
        if( PseudoF == false ) {

            for(token_i = 0; token_i < TokenN; ++token_i) {
                ANALYZER_ANALYZE(token_id);
                checksum = CHECKSUM_ACCUMULATE(checksum, token_id); 

#           if ! defined(QUEX_BENCHMARK_SERIOUS)
                printf("TokenID = %s\n", (const char*)(quex::Token::map_id_to_name(token_id)));
                printf("(%i) Checksum: %i\n", (int)token_i, (int)checksum);
#           endif
            } 
            /* Overhead-Intern: (addition, modulo division, assignment, 
             *                   increment by one, comparison) * token_n */
        } else {

            for(token_i = 0; token_i < TokenN; ++token_i) {
                ANALYZER_PSEUDO_ANALYZE(token_id);
                checksum = CHECKSUM_ACCUMULATE(checksum, token_id); 
            } 

        }
        __PRINT_END();
        ANALYZER_RESET();
    }
    /* Need to return 'checksum' so that it is not omitted by the compiler
     * because it is not used.                                             */
    return checksum;
}

void      
get_statistics(int* checksum, int* token_n, double* time_per_run_ms)
    /* The time_per_run_ms is only an estimate, not necessarily 
     * a propper measurement.                                     */
{
    int            token_id  = TKN_TERMINATION;
    const clock_t  StartTime = clock();
    clock_t        end_time  = (clock_t)-1;
    /* Run at least 200 ms */
    const clock_t  MinTime   = (clock_t)(StartTime + 0.2 * (double)CLOCKS_PER_SEC);
    double         repetition_n = 0;

    *checksum = CHECKSUM_INIT_VALUE;

    do {
        // (*) loop until the 'termination' token arrives
        for(*token_n=0; ; ++(*token_n)) {
            ANALYZER_ANALYZE(token_id);

            *checksum = CHECKSUM_ACCUMULATE(*checksum, token_id); 
#           if 1 || ! defined(QUEX_BENCHMARK_SERIOUS)
            // printf("TokenID = %s\n", (const char*)(quex::Token::map_id_to_name(token_id))); 
            printf("TokenID = %i\n", (int)token_id); 
            printf("(%i) Checksum: %i\n", (int)*token_n, (int)*checksum);
#           endif
            if( token_id == TKN_TERMINATION ) break;
        } 
        end_time = clock();
        repetition_n += 1.0;
        printf("// TokenN: %i [1]\n", (int)*token_n);
    } while( end_time < MinTime );


    *time_per_run_ms = (end_time - StartTime) / repetition_n / (double)CLOCKS_PER_SEC;
}

