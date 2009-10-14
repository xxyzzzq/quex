#include<fstream>    
#include<iostream> 
#include<cstring>


#include "TPLex"
using namespace std;
using namespace quex;

void                pseudo_analysis(quex::AnalyzerData* me);
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
        printf("CHOICES: receive-1, receive-2;\n");
        printf("SAME;\n");
#       elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN )
        printf("Token Policy UsersToken: " NAME ";\n");
        printf("CHOICES: receive-1, receive-2;\n");
        printf("SAME;\n");
#       elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE )
        printf("Token Policy UsersQueue: " NAME ";\n");
#       endif
        return 0;
    }
    cout << "NOTE: The production of an assertion error might be part of the test.\n";
    cout << "---------------------------------------------------------------------\n";
    stderr = stdout;
#   if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE) || defined(QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN)
    if( argc < 2 ) return 0;
#   endif

    TPLex         qlex("real.txt");  /* In case of pseudo_analysis the file does not matter */

#   if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
    cout << "Pseudo Analysis: Replace analysis pointer with own function.\n";
    (&qlex.engine)->current_analyzer_function = pseudo_analysis;
#   endif

    while( test_core(qlex, argv[1]) != QUEX_TKN_TERMINATION );
}

#if   defined( QUEX_OPTION_TOKEN_POLICY_QUEUE )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{
    quex::Token   token;
    quex::Token*  token_p;
    if( strcmp(Choice, "receive-1") == 0 ) {
        qlex.receive(&token);
        cout << "received: " << token.type_id_name() << endl;
        return token.type_id();
    }
    else {
        qlex.receive(&token_p);
        cout << "received: " << token_p->type_id_name() << endl;
        return token_p->type_id();
    }
}

#elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{        
    quex::Token Token;
    if( strcmp(Choice, "receive-1") == 0 ) { qlex.token = &Token; qlex.receive(); }
    else                                   qlex.receive(&Token);
    cout << "received: " << Token.type_id_name() << endl;
    return Token.type_id();
}

#elif defined( QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE )
QUEX_TYPE_TOKEN_ID test_core(TPLex& qlex, const char* Choice)
{        
    quex::Token   MyArray[5];
    quex::Token*  water_mark = qlex.receive(MyArray, MyArray + 5);

    for(quex::Token* iterator = MyArray; iterator != water_mark; ++iterator) {
        cout << "    received: " << iterator->type_id_name() << endl;
    }
    cout << "---- \n";
    return (water_mark-1)->type_id();
}

#endif

#if defined(__QUEX_OPTION_TEST_PSEUDO_ANALYSIS)
void pseudo_analysis(quex::AnalyzerData* me)
{
    TPLex&     self = *((TPLex*)me);
    static int i = 0;

    switch( i++ ) {
    default: self.send(QUEX_TKN_TERMINATION); break;
    case 0:  self.send(QUEX_TKN_ONE);         break;
    case 1:  self.send(QUEX_TKN_TWO);         break;
    case 2:  self.send(QUEX_TKN_THREE);       break;
    case 3:  self.send(QUEX_TKN_FOUR);        break;
    case 4:  self.send(QUEX_TKN_FIVE);        break;
    case 5:  self.send(QUEX_TKN______NEXT_____); break;
    case 6:  self.send(QUEX_TKN______NEXT_____); break;
    case 7:  self.send(QUEX_TKN______NEXT_____); break;
    case 8:  
             self.send(QUEX_TKN_ONE);
             self.send(QUEX_TKN______NEXT_____);
             break;
    case 9:
             self.send(QUEX_TKN_ONE);
             self.send(QUEX_TKN_TWO);
             self.send(QUEX_TKN______NEXT_____);
             break;
    case 10:
             self.send(QUEX_TKN_ONE);
             self.send(QUEX_TKN_TWO);
             self.send(QUEX_TKN_THREE);
             self.send(QUEX_TKN______NEXT_____);
             break;
    case 11:
             self.send(QUEX_TKN_ONE);
             self.send(QUEX_TKN_TWO);
             self.send(QUEX_TKN_THREE); 
             self.send(QUEX_TKN_FOUR);   
             self.send(QUEX_TKN______NEXT_____);
             break;
    case 12:
             self.send(QUEX_TKN_ONE);
             self.send(QUEX_TKN_TWO);
             self.send(QUEX_TKN_THREE); 
             self.send(QUEX_TKN_FOUR); 
             self.send(QUEX_TKN_FIVE); 
             self.send(QUEX_TKN______NEXT_____);
             break;
    }
}
#endif

