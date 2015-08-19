#include<cstdio> 
#include<cstring>

#include "TPLex"
#if ! defined(__QUEX_OPTION_PLAIN_C)
using namespace std;
using namespace quex;
#endif

__QUEX_TYPE_ANALYZER_RETURN_VALUE  pseudo_analysis(QUEX_TYPE_ANALYZER* me);
QUEX_TYPE_TOKEN_ID  test_core(TPLex&, const char*);

#if defined(QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY)
#   define UMM_NAME "(User Memory Manag.)"
#else
#   define UMM_NAME ""
#endif
#if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
#   define NAME "Pseudo Analysis;\n"
#else
#   define NAME "Real Analysis;\n"
#endif
#if   defined( QUEX_OPTION_TOKEN_POLICY_QUEUE )
#   define POLICY_NAME "queue"
#else
#   define POLICY_NAME "single"
#endif

int 
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Token Policy '" POLICY_NAME "': " UMM_NAME NAME ";\n");
        return 0;
    }
    printf("NOTE: The production of an assertion error might be part of the test.\n");
    printf("---------------------------------------------------------------------\n");
    stderr = stdout;

#   if defined(  __QUEX_OPTION_TOKEN_POLICY_IS_QUEUE_BASE)
    if( argc < 2 ) return 0;
#   endif

    /* Allocating on 'heap' allows for easier memory violation detection via 'efence' */
    TPLex*     qlex = new TPLex("real.txt");  /* In case of pseudo_analysis the file  *
                                               * does not matter.                     */
#   if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
    printf("Pseudo Analysis: Replace analysis pointer with own function.\n");
    printf("Queue Size: %i\n", QUEX_SETTING_TOKEN_QUEUE_SIZE);
    qlex->current_analyzer_function = pseudo_analysis;
#   endif

    while( test_core(*qlex, argv[1]) != QUEX_TKN_TERMINATION );

    delete qlex;
}

#if   defined( QUEX_OPTION_TOKEN_POLICY_QUEUE )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{
    QUEX_TYPE_TOKEN*  token_p;

#   if QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY
    if( qlex.token_queue_is_empty() ) {
        QUEX_TYPE_TOKEN*  begin new QUEX_TYPE_TOKEN[32];
        size_t            n     = 32;

        qley.token_queue_swap(&begin, &n);
        if( begin != 0x0 ) delete [] begin;
    }
#   endif

    qlex.receive(&token_p);

    printf("received: %s\n", token_p->type_id_name().c_str());
    QUEX_TYPE_TOKEN_ID token_id = token_p->type_id();

    return token_id;
}
#else 
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{        
    QUEX_TYPE_TOKEN   token;
    QUEX_TYPE_TOKEN*  token_p;
    token_p = qlex.token_p();

    (void)qlex.receive();

    printf("received: %s\n", token_p->type_id_name().c_str());
    QUEX_TYPE_TOKEN_ID token_id = token_p->type_id();

    return token_id;
}
#endif

#if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
__QUEX_TYPE_ANALYZER_RETURN_VALUE  pseudo_analysis(QUEX_TYPE_ANALYZER* me)
{
#   if   defined( QUEX_OPTION_TOKEN_POLICY_SINGLE)
    register QUEX_TYPE_TOKEN_ID __self_result_token_id;
#   endif
    TPLex&     self = *((TPLex*)me);
    static int i = 0;

    switch( i++ ) {
    default: self_send(QUEX_TKN_TERMINATION); break;
    case 0:  self_send(QUEX_TKN_ONE);         break;
    case 1:  self_send(QUEX_TKN_TWO);         break;
    case 2:  self_send(QUEX_TKN_THREE);       break;
    case 3:  self_send(QUEX_TKN_FOUR);        break;
    case 4:  self_send(QUEX_TKN_FIVE);        break;
    case 5:  self_send(QUEX_TKN______NEXT_____); break;
    case 6:  self_send(QUEX_TKN______NEXT_____); break;
    case 7:  self_send(QUEX_TKN______NEXT_____); break;
    case 8:  
             self_send(QUEX_TKN_ONE);
             self_send(QUEX_TKN______NEXT_____);
             break;
    case 9:
             self_send(QUEX_TKN_ONE);
             self_send(QUEX_TKN_TWO);
             self_send(QUEX_TKN______NEXT_____);
             break;
    case 10:
             self_send(QUEX_TKN_ONE);
             self_send(QUEX_TKN_TWO);
             self_send(QUEX_TKN_THREE);
             self_send(QUEX_TKN______NEXT_____);
             break;
    case 11:
             self_send(QUEX_TKN_ONE);
             self_send(QUEX_TKN_TWO);
             self_send(QUEX_TKN_THREE); 
             self_send(QUEX_TKN_FOUR);   
             self_send(QUEX_TKN______NEXT_____);
             break;
    case 12:
             self_send(QUEX_TKN_ONE);
             self_send(QUEX_TKN_TWO);
             self_send(QUEX_TKN_THREE); 
             self_send(QUEX_TKN_FOUR); 
             self_send(QUEX_TKN_FIVE); 
             self_send(QUEX_TKN______NEXT_____);
             break;
    }
#   if   defined( QUEX_OPTION_TOKEN_POLICY_SINGLE)
    return __self_result_token_id;
#   endif
}
#endif

