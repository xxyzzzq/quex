#include<cstdio> 
#include<cstring>

#include "TPLex"
#if defined(__cplusplus)
using namespace std;
using namespace quex;
#endif

__QUEX_TYPE_ANALYZER_RETURN_VALUE  pseudo_analysis(QUEX_TYPE_ANALYZER* me);
QUEX_TYPE_TOKEN_ID  test_core(TPLex&, const char*);

#if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
#   define NAME "Pseudo Analysis;\n"
#else
#   define NAME "Real Analysis;\n"
#endif

int 
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
#       if   defined( QUEX_OPTION_TOKEN_POLICY_QUEUE )
        printf("Token Policy Queue: " NAME ";\n");
        printf("SAME;\n");
#       elif defined( QUEX_OPTION_TOKEN_POLICY_SINGLE )
        printf("Token Policy UsersToken: " NAME ";\n");
        printf("SAME;\n");
#       elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE )
        printf("Token Policy UsersQueue: " NAME ";\n");
#       endif
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

    token_p = qlex.receive();
    printf("received: %s\n", token_p->type_id_name().c_str());
    return token_p->type_id();
}

#elif defined( QUEX_OPTION_TOKEN_POLICY_SINGLE )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{        
    QUEX_TYPE_TOKEN token;
    qlex.token_p_set(&token);
    (void)qlex.receive();
    printf("received: %s\n", token.type_id_name().c_str());
    return token.type_id();
}

#elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{        
    QUEX_TYPE_TOKEN   MyArray[5];
    QUEX_TYPE_TOKEN*  water_mark = qlex.receive(MyArray, MyArray + 5);

    for(QUEX_TYPE_TOKEN* iterator = MyArray; iterator != water_mark; ++iterator) {
        printf("    received: %s\n", iterator->type_id_name().c_str());
    }
    printf("---- \n");
    return (water_mark-1)->type_id();
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

