#include<fstream>    
#include<iostream> 
#include<cstring>

// The test_includer.h is created by the makefile
#include "test_includer.h"

using namespace std;

void pseudo_analysis(quex::QuexAnalyser* me);
void test();

const char* choice = "";

int 
main(int argc, char** argv) 
{
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Token Policy: Queue");
        printf("CHOICES: 1, Many;\n");
    }
    cout << "NOTE: The production of an assertion error might be part of the test.\n";
    cout << "---------------------------------------------------------------------\n";
    stderr = stdout;
    if( argc < 2 ) return 0;
    choice = argv[1];
    test();
    return 0;
}


void test()
{        
    quex::Token   Token;
    lexer         qlex("example.txt");

    int number_of_tokens = 0;

    ((quex::QuexAnalyser*)&qlex)->current_analyser_function = pseudo_analysis;

    do {
        qlex.receive(&Token);

        cout << "received: " << Token.type_id_name() << endl;

        ++number_of_tokens;

    } while( Token.type_id() != QUEX_TKN_TERMINATION );

    cout << "Number of Tokens: " << number_of_tokens << endl;
}

void pseudo_analysis(quex::QuexAnalyser* me)
{
    lexer&     self = *((lexer*)me);
    static int i = 0;

    if( strcmp(choice, "1") == 0 ) {
        switch( i++ ) {
        default: self.send(QUEX_TKN_TERMINATION); break;
        case 0:  self.send(QUEX_TKN_ONE);         break;
        case 1:  self.send(QUEX_TKN_TWO);         break;
        case 2:  self.send(QUEX_TKN_THREE);       break;
        case 3:  self.send(QUEX_TKN_FOUR);        break;
        case 4:  self.send(QUEX_TKN_FIVE);        break;
        }
    }
    else if( strcmp(choice, "Many") == 0 ) {
        switch( i++ ) {
        default: self.send(QUEX_TKN_TERMINATION); break;
        case 0:  
                 self.send(QUEX_TKN_ONE);
                 self.send(QUEX_TKN______NEXT_____);
                 break;
        case 1:
                 self.send(QUEX_TKN_ONE);
                 self.send(QUEX_TKN_TWO);
                 self.send(QUEX_TKN______NEXT_____);
                 break;
        case 2:
                 self.send(QUEX_TKN_ONE);
                 self.send(QUEX_TKN_TWO);
                 self.send(QUEX_TKN_THREE);
                 self.send(QUEX_TKN______NEXT_____);
                 break;
        case 3:
                 self.send(QUEX_TKN_ONE);
                 self.send(QUEX_TKN_TWO);
                 self.send(QUEX_TKN_THREE); 
                 self.send(QUEX_TKN_FOUR);   
                 self.send(QUEX_TKN______NEXT_____);
                 break;
        case 4:
                 self.send(QUEX_TKN_ONE);
                 self.send(QUEX_TKN_TWO);
                 self.send(QUEX_TKN_THREE); 
                 self.send(QUEX_TKN_FOUR); 
                 self.send(QUEX_TKN_FIVE); 
                 self.send(QUEX_TKN______NEXT_____);
                 break;
        }
    }
}

