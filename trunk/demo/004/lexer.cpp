
#include "main.h"

#ifndef QUEX_BENCHMARK_SERIOUS
void __PRINT_END()
{ printf("`------------------------------------------------------------------------------------\n"); }
#else 
#   define __PRINT_END() /* empty */
#endif

double
benchmark(GetTokenIDFuncP FuncP_get_token_id, ResetFuncP FuncP_reset, 
          const clock_t MinExperimentTime,
          size_t TokenN, int CheckSum, double* repetition_n)
{
    register int   token_id     = TKN_TERMINATION;
    //
    // -- repeat the experiment, so that it takes at least 20 seconds
    const clock_t  StartTime    = clock();
    const clock_t  EndTime      = StartTime + MinExperimentTime;
    clock_t        current_time = 0;
    int            checksum     = 0;

    do { 
        checksum       = 777;
        *repetition_n += 1.0f;
        
        for(size_t token_i = 0; token_i < TokenN; ++token_i) {
            token_id = FuncP_get_token_id();

            // checksum = (checksum + TokenP->type_id()) % 0xFF; 
            checksum = (checksum + token_id) % 0xFF; 

#           if ! defined(QUEX_BENCHMARK_SERIOUS)
            cout << /*qlex.line_number() << ": " <<*/ quex::Token::map_id_to_name(token_id) << endl;
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
                printf("Weird World.\n");
                exit(-1);
            }
        }
        FuncP_reset();

        current_time = clock();
    } while( current_time < EndTime );
    
    return current_time - StartTime;
}

size_t
count_token_n(GetTokenIDFuncP FuncP_get_token_id, int* checksum)
{
    int token_id = TKN_TERMINATION;
    int token_n = 0;
    *checksum = 0;

    // (*) loop until the 'termination' token arrives
    for(token_n=0; ; ++token_n) {
        token_id = FuncP_get_token_id();
        *checksum = (*checksum + token_id) % 0xFF; 
        if( token_id == TKN_TERMINATION ) break;
    } 
    printf("// TokenN: %i [1]\n", token_n);
    return token_n;
}

