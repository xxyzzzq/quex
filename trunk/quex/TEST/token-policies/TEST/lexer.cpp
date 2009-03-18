#include<fstream>    
#include<iostream> 
#include<cstring>

// The test_includer.h is created by the makefile
#include "test_includer.h"

using namespace std;

void pseudo_analysis(lexer*);
void test();

int 
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Token Policy: Queue");
    }
    test();
    return 0;
}


void test()
{        
    quex::Token   Token;
    lexer   qlex("example.txt");

    int number_of_tokens = 0;

    ((quex::QuexAnalyser*)&qlex)->current_analyser_function = (quex::QUEX_TYPE_ANALYZER_FUNCTION)pseudo_analysis;

    do {
        qlex.receive(&Token);

        cout << Token.type_id_name() << endl;

        ++number_of_tokens;

    } while( Token.type_id() != QUEX_TKN_TERMINATION );

    cout << "Number of Tokens: " << number_of_tokens << endl;
}

void pseudo_analysis(lexer* me)
{
    static int i = 0;
    lexer&     self = *me;  // to be uniform with the generated code

    switch( i++ ) {
    default: self.send(QUEX_TKN_TERMINATION); break;
    case 0:  self.send(QUEX_TKN_ONE);         break;
    case 1:  self.send(QUEX_TKN_TWO);         break;
    case 2:  self.send(QUEX_TKN_THREE);       break;
    case 3:  self.send(QUEX_TKN_FOUR);        break;
    case 4:  self.send(QUEX_TKN_FIVE);        break;
    }

    
}

