#include<fstream>    
#include<iostream> 

#include <./lexer>

using namespace std;

void pseudo_analysis(quex::lexer*);

int 
main(int argc, char** argv) 
{

}

void
analysis()
{        
    quex::Token   Token;
    quex::lexer   qlex("example.txt");

    int number_of_tokens = 0;

    ((quex::QuexAnalyser*)&qlex)->current_analyser_function = (QUEX_TYPE_ANALYZER_FUNCTION*)pseudo_analysis;

    do {
        qlex.receive(&Token);

        cout << Token.type_id_name() << endl;

        ++number_of_tokens;

    } while( Token.type_id() != QUEX_TKN_TERMINATION );

    return 0;
}
