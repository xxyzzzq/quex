#include<fstream>    
#include<iostream> 
#include<cstring>
#include<cstdio>

#include "EHLexer"

using namespace std;

int 
main(int argc, char** argv) 
{        

    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf(__TEST_DESCRIPTION ";\n");
        printf("CHOICES: " __TEST_CHOICES ";\n");
        return 0;
    }
    quex::Token*   token;
    std::string    Directory("examples/");
    quex::EHLexer  qlex(Directory + argv[1] + ".txt");

    cerr << "| [START]\n";

    token = qlex.token_p();
    do {
        (void)qlex.receive();
        cerr << "TOKEN: " << std::string(*token) << endl;
    } while( token->type_id() != TK_TERMINATION );

    cerr << "| [END]\n";

    return 0;
}
